import torch
import torch_multilabel_embedding as tml


class SimiLossW2V(torch.nn.Module):
    def __init__(self,
                 embedding: torch.Tensor = None,
                 vocab_size: int = None,
                 embed_size: int = None,
                 context_size: int = None,
                 random_state: int = None,
                 **kwargs):
        super(SimiLossW2V, self).__init__()

        # store hyper params
        if embedding is None:
            self.vocab_size = vocab_size  # v
            self.embed_size = embed_size  # e
        else:
            self.vocab_size, self.embed_size = embedding.shape
        self.context_size = context_size  # m

        # init embedding layer
        self.emb = tml.MultiLabelEmbedding(
            vocab_size=self.vocab_size,
            embed_size=self.embed_size,
            random_state=random_state,
            **kwargs)

        # set pretrained embedding weights
        if embedding is None:
            # Normal distribution N(mu=0, sig=0.274..)
            torch.nn.init.normal_(
                self.emb.weight, mean=0.0, std=0.2745960056781769)
        else:
            self.emb.weight.data = embedding
            # self.emb.weight = torch.nn.parameter.Parameter(
            #     torch.tensor(embedding, dtype=torch.float32))

        # trainable weighting scheme for context inputs
        self.ctx_scheme = torch.nn.parameter.Parameter(
            torch.empty(self.context_size))
        # equal-size
        torch.nn.init.constant_(
            self.ctx_scheme, 1.0 / self.context_size)

        # trainable similarity kernel
        self.simi_kernel = torch.nn.parameter.Parameter(
            torch.empty((self.embed_size, self.embed_size)))
        # Xavier for linear layers
        torch.nn.init.xavier_normal_(self.simi_kernel, gain=1.0)

        # initialize layer weights
        if random_state:
            torch.manual_seed(random_state)

    def get_indices(self, max_idx: int):
        # precompute indicies
        trgt_idx = self.context_size // 2
        ctx_idx = list(range(self.context_size + 1))
        ctx_idx.remove(trgt_idx)
        # add range indicies
        indices = torch.arange(max_idx)
        ctx_idx = indices.repeat(self.context_size, 1).t() \
            + torch.tensor(ctx_idx).repeat(max_idx, 1)
        trgt_idx = indices + torch.tensor(trgt_idx)
        return trgt_idx, ctx_idx

    def trainable_embedding(self, trainable):
        for param in self.emb.parameters():
            param.requires_grad = trainable

    def _similarity_score(self, b, C):
        """
        Parameters:
        -----------
        b : torch.tensor[batch_sz, embed_sz]
          The target vector

        C : torch.tensor[batch_sz, context_sz, embed_sz]
          Context vectors (Basically the features `X` to predict `y`)

        Formula:
        --------
            wC : Context weighting scheme (trainable)
            mS : Similarity kernel matrix (trainable)

            h = wC * C
            f = h*mS*b^T
        """
        # apply (trained) weighting scheme to context emb. vectors
        h = torch.nn.functional.softmax(self.ctx_scheme, dim=0)
        h = torch.matmul(h, C)
        # compute similarity score
        f = torch.matmul(h, self.simi_kernel)
        f = torch.mul(b, h).sum(axis=1)
        return f

    def forward(self, b, C, nb, nC):
        b = self.emb(b)
        C = self.emb(C)
        nb = self.emb(nb)
        nC = self.emb(nC)

        # similarity functions
        po = self._similarity_score(b, C)
        n1 = self._similarity_score(nb, C)
        n2 = self._similarity_score(b, nC)

        # L1 Penalty
        l1 = 0.1 * self.simi_kernel.pow(2).mean()

        # contrastive loss function
        return (-po + .5 * n1 + .5 * n2).mean() + l1
