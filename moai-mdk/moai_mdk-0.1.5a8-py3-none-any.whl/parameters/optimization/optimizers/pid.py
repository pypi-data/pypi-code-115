import torch
import typing

__all__ = ['PID']

#NOTE: from https://github.com/jettify/pytorch-optimizer/blob/master/torch_optimizer/pid.py

class PID(torch.optim.Optimizer):
    r"""Implements PID optimization algorithm.
    
    - **Paper**: [A PID Controller Approach for Stochastic Optimization of Deep Networks](https://csjunxu.github.io/paper/TNNLS2020.PDF)
    - **Implementation**: [GitHub @ jettify](https://github.com/jettify/pytorch-optimizer)    

    Arguments:
        params: iterable of parameters to optimize or dicts defining
            parameter groups
        lr: learning rate (default: 1e-3)
        momentum: momentum factor (default: 0.0)
        weight_decay: weight decay (L2 penalty) (default: 0.0)
        dampening: dampening for momentum (default: 0.0)
        derivative: D part of the PID (default: 10.0)
        integral: I part of the PID (default: 5.0)

    Example:
        >>> import torch_optimizer as optim
        >>> optimizer = optim.PID(model.parameters(), lr=0.001, momentum=0.1)
        >>> optimizer.zero_grad()
        >>> loss_fn(model(input), target).backward()
        >>> optimizer.step()

    __ http://www4.comp.polyu.edu.hk/~cslzhang/paper/CVPR18_PID.pdf

    Note:
        Reference code: https://github.com/tensorboy/PIDOptimizer
    """

    def __init__(self,
        params: typing.Iterator[torch.nn.Parameter],
        lr: float=1e-3,
        momentum: float=0.0,
        dampening: float=0,
        weight_decay: float=0.0,
        integral: float=5.0,
        derivative: float=10.0,
    ) -> None:
        defaults = dict(
            lr=lr,
            momentum=momentum,
            dampening=dampening,
            weight_decay=weight_decay,
            integral=integral,
            derivative=derivative,
        )
        if lr <= 0.0:
            raise ValueError('Invalid learning rate: {}'.format(lr))
        if momentum < 0.0:
            raise ValueError('Invalid momentum value: {}'.format(momentum))
        if weight_decay < 0.0:
            raise ValueError(
                'Invalid weight_decay value: {}'.format(weight_decay)
            )
        if integral < 0.0:
            raise ValueError('Invalid PID integral value: {}'.format(integral))
        if derivative < 0.0:
            raise ValueError(
                'Invalid PID derivative value: {}'.format(derivative)
            )

        super(PID, self).__init__(params, defaults)

    def step(self, closure: typing.Optional[typing.Callable[[], float]]=None) -> typing.Optional[float]:
        r"""Performs a single optimization step.

        Arguments:
            closure: A closure that reevaluates the model and returns the loss.
        """
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            weight_decay = group['weight_decay']
            momentum = group['momentum']
            dampening = group['dampening']
            integral = group['integral']
            derivative = group['derivative']
            for p in group['params']:
                if p.grad is None:
                    continue
                d_p = p.grad.data
                if weight_decay != 0:
                    d_p.add_(p.data, alpha=weight_decay)
                if momentum != 0:
                    param_state = self.state[p]
                    if 'i_buffer' not in param_state:
                        i_buf = param_state['i_buffer'] = torch.zeros_like(p)
                        i_buf.mul_(momentum).add_(d_p)
                    else:
                        i_buf = param_state['i_buffer']
                        i_buf.mul_(momentum).add_(d_p, alpha=1 - dampening)
                    if 'grad_buffer' not in param_state:
                        g_buf = param_state['grad_buffer'] = torch.zeros_like(
                            p
                        )
                        g_buf = d_p

                        d_buf = param_state['d_buffer'] = torch.zeros_like(p)
                        d_buf.mul_(momentum).add_(d_p - g_buf)
                    else:
                        d_buf = param_state['d_buffer']
                        g_buf = param_state['grad_buffer']
                        d_buf.mul_(momentum).add_(
                            d_p - g_buf, alpha=1 - momentum
                        )
                        self.state[p]['grad_buffer'] = d_p.clone()

                    d_p = d_p.add_(i_buf, alpha=integral).add_(
                        d_buf, alpha=derivative
                    )
                p.data.add_(d_p, alpha=-group['lr'])
        return loss