import math
import torch
import torch.nn as nn
import typing

__all__ = ['Yogi']

#NOTE: from https://github.com/jettify/pytorch-optimizer/blob/master/torch_optimizer/yogi.py

class Yogi(torch.optim.Optimizer):
    r"""Implements Yogi Optimizer Algorithm.

    - **Paper**: [Adaptive methods for Nonconvex Optimization](https://papers.nips.cc/paper/8186-adaptive-methods-for-nonconvex-optimization.pdf)
    - **Implementation**: [GitHub @ jettify](https://github.com/jettify/pytorch-optimizer)    

    Arguments:
        params: iterable of parameters to optimize or dicts defining
            parameter groups
        lr: learning rate (default: 1e-2)
        betas: coefficients used for computing
            running averages of gradient and its square (default: (0.9, 0.999))
        eps: term added to the denominator to improve
            numerical stability (default: 0.001)
        initial_accumulator: initial values for first and
            second moments (default: 1e-6)
        weight_decay: weight decay (L2 penalty) (default: 0)

    Example:
        >>> import torch_optimizer as optim
        >>> optimizer = optim.Yogi(model.parameters(), lr=0.01)
        >>> optimizer.zero_grad()
        >>> loss_fn(model(input), target).backward()
        >>> optimizer.step()

    __ https://papers.nips.cc/paper/8186-adaptive-methods-for-nonconvex-optimization  # noqa

    Note:
        Reference code: https://github.com/4rtemi5/Yogi-Optimizer_Keras
    """

    def __init__(self,
        params: typing.Iterator[torch.nn.Parameter],
        lr: float=1e-2,
        betas: typing.Tuple[float, float]=(0.9, 0.999),
        eps: float=1e-3,
        initial_accumulator: float=1e-6,
        weight_decay: float=0,
    ) -> None:
        if lr <= 0.0:
            raise ValueError('Invalid learning rate: {}'.format(lr))
        if eps < 0.0:
            raise ValueError('Invalid epsilon value: {}'.format(eps))
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(
                'Invalid beta parameter at index 0: {}'.format(betas[0])
            )
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(
                'Invalid beta parameter at index 1: {}'.format(betas[1])
            )
        if weight_decay < 0:
            raise ValueError(
                'Invalid weight_decay value: {}'.format(weight_decay)
            )

        defaults = dict(
            lr=lr,
            betas=betas,
            eps=eps,
            initial_accumulator=initial_accumulator,
            weight_decay=weight_decay,
        )
        super(Yogi, self).__init__(params, defaults)

    def step(self, closure: typing.Optional[typing.Callable[[], float]]=None) -> typing.Optional[float]:
        r"""Performs a single optimization step.

        Arguments:
            closure: A closure that reevaluates the model and returns the loss.
        """
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None:
                    continue
                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError(
                        'Yogi does not support sparse gradients, '
                        'please consider SparseAdam instead'
                    )

                state = self.state[p]

                # State initialization
                # Followed from official implementation in tensorflow addons:
                # https://github.com/tensorflow/addons/blob/master/tensorflow_addons/optimizers/yogi.py#L118 # noqa
                # For more details refer to the discussion:
                # https://github.com/jettify/pytorch-optimizer/issues/77
                if len(state) == 0:
                    state['step'] = 0
                    # Exponential moving average of gradient values
                    state['exp_avg'] = nn.init.constant_(
                        torch.empty_like(
                            p.data, memory_format=torch.preserve_format
                        ),
                        group['initial_accumulator'],
                    )
                    # Exponential moving average of squared gradient values
                    state['exp_avg_sq'] = nn.init.constant_(
                        torch.empty_like(
                            p.data, memory_format=torch.preserve_format
                        ),
                        group['initial_accumulator'],
                    )

                exp_avg, exp_avg_sq = state['exp_avg'], state['exp_avg_sq']
                beta1, beta2 = group['betas']

                state['step'] += 1
                bias_correction1 = 1 - beta1 ** state['step']
                bias_correction2 = 1 - beta2 ** state['step']

                if group['weight_decay'] != 0:
                    grad = grad.add(p.data, alpha=group['weight_decay'])

                # Decay the first and second moment running average coefficient
                exp_avg.mul_(beta1).add_(grad, alpha=1 - beta1)

                grad_squared = grad.mul(grad)

                exp_avg_sq.addcmul_(
                    torch.sign(exp_avg_sq - grad_squared),
                    grad_squared,
                    value=-(1 - beta2),
                )

                denom = (exp_avg_sq.sqrt() / math.sqrt(bias_correction2)).add_(
                    group['eps']
                )
                step_size = group['lr'] / bias_correction1
                p.data.addcdiv_(exp_avg, denom, value=-step_size)

        return loss