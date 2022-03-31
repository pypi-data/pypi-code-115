import enum
from ..attention import MultiHeadAttentionLayer
from ..normalization import LayerNorm as BertLayerNorm
import torch.nn as nn
from ..activation import activations


class BertIntermediate(nn.Module):
    def __init__(self, hidden_size, intermediate_size, hidden_act) -> None:
        super().__init__()
        self.dense = nn.Linear(hidden_size, intermediate_size)
        self.intermediate_act_fn = activations[hidden_act]

    def forward(self, hidden_states):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.intermediate_act_fn(hidden_states)
        return hidden_states


class BertAddNorm(nn.Module):
    def __init__(self, intermediate_size, hidden_size, hidden_dropout_prob, layer_norm_eps) -> None:
        super().__init__()
        self.dense = nn.Linear(intermediate_size, hidden_size)
        self.dropout = nn.Dropout(hidden_dropout_prob)
        self.layer_norm = BertLayerNorm(hidden_size=hidden_size, eps=layer_norm_eps)

    def forward(self, hidden_states, input_tensor):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.layer_norm(hidden_states + input_tensor)
        return hidden_states

class BertAttention(nn.Module):
    def __init__(
        self, 
        hidden_size, 
        num_attention_heads, 
        attention_probs_dropout_prob, 
        return_attention_scores,
        hidden_dropout_prob,
        layer_norm_eps) -> None:
        super().__init__()
        self.self = MultiHeadAttentionLayer(hidden_size, num_attention_heads, attention_probs_dropout_prob, attention_scale, return_attention_scores)
        self.output = BertAddNorm(
            intermediate_size=hidden_size,
            hidden_size=hidden_size,
            hidden_dropout_prob=hidden_dropout_prob,
            layer_norm_eps=layer_norm_eps
            )
    def forward(self, input_tensor, attention_mask=None, head_mask=None):
        self_outputs = self.self(input_tensor, input_tensor, input_tensor, attention_mask, head_mask)
        attention_output = self.output(self_outputs[0], input_tensor)
        outputs = (attention_output,) + self_outputs[1:]
        return outputs


class BertLayer(nn.Module):
    def __init__(
        self,
        hidden_size,
        num_attention_heads,
        attention_probs,
        hidden_act,
        intermediate_size,
        hidden_dropout_prob,
        layer_norm_eps
        ) -> None:
        super().__init__()
        self.attention = BertAttention(
            hidden_size=hidden_size,
            num_attention_heads=num_attention_heads,
            attention_probs_dropout_prob=attention_probs
        )
        self.intermediate = BertIntermediate(hidden_size=hidden_size,intermediate_size=intermediate_size, hidden_act=hidden_act)
        self.output = BertAddNorm(intermediate_size, hidden_size, hidden_dropout_prob, layer_norm_eps)

    def forward(self, hidden_states, attention_mask=None, head_mask=None):
        attention_outputs = self.attention(hidden_states, attention_mask, head_mask)
        attention_output = attention_outputs[0]

        # 这里是左上的 Add & Norm，从而得到完整的 FFN
        intermediate_output = self.intermediate(attention_output)
        layer_output = self.output(intermediate_output, attention_output)

        # attention_outputs[0] 是 embedding, [1] 是 attention_probs
        outputs = (layer_output,) + attention_outputs[1:]
        return outputs


class BertEncoder(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layer = nn.ModuleList([BertLayer()])
        


    def forward(self, hidden_states, attention_mask=None, head_mask=None):
        all_hidden_states = ()
        all_attentions = ()
        for i, layer_module in enumerate(self.layer):
            pass




