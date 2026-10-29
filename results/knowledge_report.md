# Knowledge probe

## Share of models answering 'yes'

|                                  |   control |   event, after cutoff |   event, knowable |
|:---------------------------------|----------:|----------------------:|------------------:|
| ('bankruptcy', 'gemini25flash')  |     0.017 |                 0     |             0.434 |
| ('bankruptcy', 'gpt41mini')      |     0.001 |                 0     |             0.128 |
| ('bankruptcy', 'gpt4omini')      |     0.003 |                 0.019 |             0.25  |
| ('bankruptcy', 'haiku55')        |     0.016 |                 1     |             0.461 |
| ('bankruptcy', 'llama33')        |     0.022 |                 0.053 |             0.333 |
| ('bankruptcy', 'llama4')         |     0.087 |                 0.156 |             0.495 |
| ('restatement', 'gemini25flash') |     0.028 |                 0.021 |             0.089 |
| ('restatement', 'gpt41mini')     |     0.002 |                 0     |             0     |
| ('restatement', 'gpt4omini')     |     0     |                 0     |             0.017 |
| ('restatement', 'haiku55')       |     0.01  |               nan     |             0.041 |
| ('restatement', 'llama33')       |     0     |                 0     |             0.026 |
| ('restatement', 'llama4')        |     0.031 |                 0.022 |             0.058 |

## First stage: extra 'yes' when the outcome is knowable

| measure     |   gamma |     se |   p_value |   n_identifying_units |
|:------------|--------:|-------:|----------:|----------------------:|
| pooled      |  0.0423 | 0.0166 |    0.0108 |                   352 |
| bankruptcy  |  0.149  | 0.0422 |    0.0004 |                   105 |
| restatement | -0.0083 | 0.0126 |    0.5119 |                   247 |

## Leakage among models that knew the outcome

`gamma` = leakage when the model did not report knowing the outcome; `moderator_interaction` = additional leakage when it did.

| task                        | level       |   share_knowable_known |   gamma |   moderator_interaction |   moderator_se |   moderator_p |
|:----------------------------|:------------|-----------------------:|--------:|------------------------:|---------------:|--------------:|
| predict                     | generalised |                 0.1323 | -0.0003 |                  0.0167 |         0.0137 |        0.2221 |
| predict                     | names       |                 0.1323 | -0.0066 |                  0.0123 |         0.0138 |        0.373  |
| predict                     | paraphrased |                 0.1323 | -0.0027 |                 -0.0166 |         0.0092 |        0.0719 |
| predict                     | raw         |                 0.1323 | -0.005  |                  0.0176 |         0.0131 |        0.1781 |
| construct                   | generalised |                 0.1553 |  0.0229 |                 -0.0016 |         0.0596 |        0.979  |
| construct                   | names       |                 0.1553 |  0.0078 |                  0.0064 |         0.0533 |        0.9044 |
| construct                   | paraphrased |                 0.1553 | -0.0539 |                  0.0812 |         0.0628 |        0.1959 |
| construct                   | raw         |                 0.1553 | -0.0088 |                  0.0687 |         0.0561 |        0.2208 |
| predict_bankruptcy          | generalised |                 0.38   | -0.0043 |                  0.0369 |         0.0186 |        0.047  |
| predict_bankruptcy          | names       |                 0.38   | -0.0025 |                  0.0282 |         0.0176 |        0.1091 |
| predict_bankruptcy          | paraphrased |                 0.38   | -0.0148 |                 -0.0045 |         0.0138 |        0.7476 |
| predict_bankruptcy          | raw         |                 0.38   |  0.0021 |                  0.0303 |         0.0175 |        0.0839 |
| construct_bankruptcy_events | generalised |                 0.38   | -0.0742 |                 -0.0184 |         0.0772 |        0.8119 |
| construct_bankruptcy_events | names       |                 0.38   | -0.1519 |                 -0.0133 |         0.0723 |        0.8542 |
| construct_bankruptcy_events | paraphrased |                 0.38   | -0.1557 |                 -0.0067 |         0.0889 |        0.9395 |
| construct_bankruptcy_events | raw         |                 0.38   | -0.1581 |                  0.0154 |         0.0803 |        0.8483 |
