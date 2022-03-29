from . import WMLDeployment

import pytorch_lightning as pl
import torch
import torch.nn as nn
import torch.nn.functional as F
from pytorch_lightning.metrics import Accuracy
from sklearn.datasets import load_iris
from torch.utils.data import DataLoader, random_split, TensorDataset


class IrisClassification(pl.LightningModule):
    def __init__(self, **kwargs):
        super().__init__()

        self.train_acc = Accuracy()
        self.val_acc = Accuracy()
        self.test_acc = Accuracy()
        self.args = kwargs

        self.fc1 = nn.Linear(4, 10)
        self.fc2 = nn.Linear(10, 10)
        self.fc3 = nn.Linear(10, 3)
        self.cross_entropy_loss = nn.CrossEntropyLoss()

        self.lr = kwargs.get("lr", 0.01)
        self.momentum = kwargs.get("momentum", 0.9)
        self.weight_decay = kwargs.get("weight_decay", 0.1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return x

    def configure_optimizers(self):
        return torch.optim.SGD(
            self.parameters(), lr=self.lr, momentum=self.momentum, weight_decay=self.weight_decay
        )

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        loss = self.cross_entropy_loss(logits, y)
        self.train_acc(torch.argmax(logits, dim=1), y)
        self.log("train_acc", self.train_acc.compute(), on_step=False, on_epoch=True)
        self.log("loss", loss)
        return {"loss": loss}

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        loss = F.cross_entropy(logits, y)
        self.val_acc(torch.argmax(logits, dim=1), y)
        self.log("val_acc", self.val_acc.compute())
        self.log("val_loss", loss, sync_dist=True)

    def test_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        loss = F.cross_entropy(logits, y)
        self.test_acc(torch.argmax(logits, dim=1), y)
        self.log("test_loss", loss)
        self.log("test_acc", self.test_acc.compute())


class IrisDataModule(pl.LightningDataModule):
    def __init__(self):
        super().__init__()
        self.columns = None

    def _get_iris_as_tensor_dataset(self):
        iris = load_iris()
        df = iris.data
        self.columns = iris.feature_names
        target = iris["target"]
        data = torch.Tensor(df).float()
        labels = torch.Tensor(target).long()
        data_set = TensorDataset(data, labels)
        return data_set

    def setup(self, stage=None):

        # Assign train/val datasets for use in dataloaders
        if stage == "fit" or stage is None:
            iris_full = self._get_iris_as_tensor_dataset()
            self.train_set, self.val_set = random_split(iris_full, [130, 20])

        # Assign test dataset for use in dataloader(s)
        if stage == "test" or stage is None:
            self.train_set, self.test_set = random_split(self.train_set, [110, 20])

    def train_dataloader(self):
        return DataLoader(self.train_set, batch_size=4)

    def val_dataloader(self):
        return DataLoader(self.val_set, batch_size=4)

    def test_dataloader(self):
        return DataLoader(self.test_set, batch_size=4)

class MulticlassIrisPytorch(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisPytorch,self).__init__(name="Spark Iris Pytorch",
            asset_name="Spark Iris Pytorch",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):

        params = {} #{"lr": 0.1, "momentum": 0.9, "weight_decay": 0}

        model = IrisClassification(**params)
        dm = IrisDataModule()
        dm.setup(stage="fit")
        trainer = pl.Trainer(max_epochs=5)
        trainer.fit(model, dm)