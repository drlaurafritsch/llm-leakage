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
| pooled      |  0.0416 | 0.0167 |    0.0126 |                   352 |
| bankruptcy  |  0.1487 | 0.0422 |    0.0004 |                   105 |
| restatement | -0.0089 | 0.0128 |    0.4845 |                   247 |

## Leakage among models that knew the outcome

`gamma` = leakage when the model did not report knowing the outcome; `moderator_interaction` = additional leakage when it did.

| task                        | level       |   share_knowable_known |   gamma |   moderator_interaction |   moderator_se |   moderator_p |
|:----------------------------|:------------|-----------------------:|--------:|------------------------:|---------------:|--------------:|
| predict                     | generalised |                 0.1323 | -0.0015 |                  0.0213 |         0.0134 |        0.1118 |
| predict                     | names       |                 0.1323 | -0.0082 |                  0.0175 |         0.0135 |        0.1956 |
| predict                     | paraphrased |                 0.1323 | -0.0029 |                 -0.0152 |         0.0091 |        0.0957 |
| predict                     | raw         |                 0.1323 | -0.0066 |                  0.0227 |         0.0129 |        0.0773 |
| construct                   | generalised |                 0.1553 |  0.0369 |                 -0.0399 |         0.0592 |        0.5002 |
| construct                   | names       |                 0.1553 |  0.0225 |                 -0.0307 |         0.0532 |        0.5637 |
| construct                   | paraphrased |                 0.1553 | -0.0359 |                  0.0324 |         0.0616 |        0.5988 |
| construct                   | raw         |                 0.1553 |  0.0049 |                  0.0347 |         0.0557 |        0.5334 |
| predict_bankruptcy          | generalised |                 0.38   | -0.014  |                  0.0424 |         0.0194 |        0.0287 |
| predict_bankruptcy          | names       |                 0.38   | -0.0137 |                  0.0344 |         0.0187 |        0.0658 |
| predict_bankruptcy          | paraphrased |                 0.38   | -0.0201 |                 -0.0033 |         0.0141 |        0.8133 |
| predict_bankruptcy          | raw         |                 0.38   | -0.0093 |                  0.0366 |         0.0186 |        0.0492 |
| construct_bankruptcy_events | generalised |                 0.38   | -0.061  |                 -0.0245 |         0.0749 |        0.7437 |
| construct_bankruptcy_events | names       |                 0.38   | -0.1389 |                 -0.0193 |         0.0704 |        0.7838 |
| construct_bankruptcy_events | paraphrased |                 0.38   | -0.1385 |                 -0.0184 |         0.0866 |        0.8318 |
| construct_bankruptcy_events | raw         |                 0.38   | -0.1473 |                  0.0118 |         0.0772 |        0.8789 |
