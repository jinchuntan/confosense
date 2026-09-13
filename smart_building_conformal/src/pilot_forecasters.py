"""The existing Attention-LSTM architecture with lazy, bounded CPU batches."""
from __future__ import annotations
import io
import math
import numpy as np
import torch
from .attention_lstm import AttentionLSTM, set_determinism
from .pilot_resources import require_ram


class Persistence:
    estimator_class = "src.pilot_forecasters.Persistence"
    def __init__(self, columns):
        self.column = next(c for c in columns if c.endswith("target_lag_0"))
    def predict(self, X):
        return X[self.column].to_numpy(float)


class LazyLSTM:
    estimator_class = "src.attention_lstm.AttentionLSTM"

    def fit(self, data, train_rows, params, seed, *, validation_rows=None,
            final_epochs=None, memory_floor=0, progress=None):
        set_determinism(seed)
        self.params, self.seed = dict(params), seed
        seq, mapping, y = data["lazy"], data["sequence_rows"], data["y"]
        batch = int(params["batch_size"])
        total = np.zeros(seq.n_features); squares = total.copy(); count = 0
        for start in range(0,len(train_rows),batch):
            a = seq.take(mapping[train_rows[start:start+batch]]).astype(np.float64)
            total += a.sum(axis=(0,1)); squares += np.square(a).sum(axis=(0,1))
            count += a.shape[0]*a.shape[1]
        self.mean = total/count
        self.std = np.sqrt(np.maximum(0,squares/count-self.mean**2))
        self.std[self.std < 1e-12] = 1.
        self.y_mean = float(y[train_rows].mean()); self.y_std = float(y[train_rows].std() or 1.)
        self.model = AttentionLSTM(seq.n_features, params["hidden_size"], params["dropout"])
        optimiser = torch.optim.Adam(self.model.parameters(), lr=params["learning_rate"])
        loss_fn = torch.nn.MSELoss(); generator = torch.Generator().manual_seed(seed)
        best, best_state, stale = float("inf"), None, 0
        epochs = int(final_epochs if final_epochs is not None else params["max_epochs"])
        self.history = []; self.best_epoch = epochs
        for epoch in range(epochs):
            if memory_floor:
                require_ram(memory_floor)
            self.model.train(); perm = torch.randperm(len(train_rows), generator=generator).numpy()
            total_loss=0.
            for start in range(0,len(perm),batch):
                rows = train_rows[perm[start:start+batch]]
                xx=self.tensor(seq.take(mapping[rows]))
                yy=torch.as_tensor((y[rows]-self.y_mean)/self.y_std,dtype=torch.float32)
                optimiser.zero_grad(set_to_none=True)
                pred=self.model(xx); loss=loss_fn(pred,yy)
                loss.backward(); optimiser.step()
                total_loss += float(loss.detach())*len(rows)
            entry=dict(epoch=epoch+1, train_mse=total_loss/len(train_rows))
            if validation_rows is not None:
                val=self.predict(data,validation_rows,batch)
                score=float(np.mean(np.abs(y[validation_rows]-val))); entry["validation_mae"]=score
                if score < best - 1e-6:
                    best=score; stale=0; self.best_epoch=epoch+1
                    best_state={k:v.detach().clone() for k,v in self.model.state_dict().items()}
                else:
                    stale+=1
            self.history.append(entry)
            if progress is not None and ((epoch+1)%5 == 0 or epoch == 0):
                progress(entry)
            if validation_rows is not None and stale >= params["patience"]:
                break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        return self

    def tensor(self, a):
        return torch.as_tensor(((a-self.mean)/self.std).astype(np.float32))

    def predict(self,data,rows,batch):
        self.model.eval(); out=[]
        with torch.inference_mode():
            for start in range(0,len(rows),batch):
                xx=data["lazy"].take(data["sequence_rows"][rows[start:start+batch]])
                out.append(self.model(self.tensor(xx)).numpy()*self.y_std+self.y_mean)
        return np.concatenate(out).astype(float) if out else np.array([],float)

    def artifact(self):
        buffer=io.BytesIO()
        torch.save(dict(state_dict=self.model.state_dict(), parameters=self.params, seed=self.seed,
            input_features=self.model.input_proj.in_features, x_mean=self.mean.tolist(), x_std=self.std.tolist(),
            y_mean=self.y_mean,y_std=self.y_std,estimator_class=self.estimator_class),buffer)
        return buffer.getvalue()


def predict(model,name,data,rows,batch):
    if name == "attention_lstm":
        return model.predict(data,rows,batch)
    out=[]
    for start in range(0,len(rows),batch):
        out.append(model.predict(data["X"].iloc[rows[start:start+batch]]))
    return np.concatenate(out).astype(float)


def fit(name,data,train,params,seed,*,validation=None,final_epochs=None,memory_floor=0,progress=None):
    if name == "persistence":
        return Persistence(data["X"].columns)
    if name == "xgboost":
        from xgboost import XGBRegressor
        model=XGBRegressor(**params,objective="reg:squarederror",tree_method="hist",random_state=seed,n_jobs=1)
        model.fit(data["X"].iloc[train],data["y"][train])
        return model
    if name == "attention_lstm":
        return LazyLSTM().fit(data,train,params,seed,validation_rows=validation,
            final_epochs=final_epochs,memory_floor=memory_floor,progress=progress)
    raise ValueError(f"unknown pilot model {name}")


def actual_identity(model):
    return getattr(model,"estimator_class",type(model).__module__+"."+type(model).__name__)


def select_candidate(records):
    """Equal inner-fold weight; exact ties follow frozen candidate-list order."""
    candidates=sorted({r["candidate_id"] for r in records})
    scores=[]
    for c in candidates:
        rows=[r for r in records if r["candidate_id"]==c]
        if sorted(r["inner_fold"] for r in rows) != [0,1]:
            raise ValueError("candidate lacks exactly two inner validation folds")
        scores.append((float(np.mean([r["mae"] for r in rows])),c))
    if not np.isfinite([v for v,_ in scores]).all():
        raise ValueError("nonfinite inner tuning score")
    _,chosen=min(scores)
    epochs=[r["best_epoch"] for r in records if r["candidate_id"]==chosen and r.get("best_epoch") is not None]
    return chosen, (int(math.ceil(np.mean(epochs))) if epochs else None), scores
