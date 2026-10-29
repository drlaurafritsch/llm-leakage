# Leakage report

## construct: financial_distress
- **raw**: No detectable leakage: estimate -0.00 SD, 95% CI [-0.0934, 0.0841] in score units. The design could detect effects of 0.07 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate +0.00 SD, 95% CI [-0.0843, 0.101] in score units. The design could detect effects of 0.07 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate +0.01 SD, 95% CI [-0.0658, 0.112] in score units. The design could detect effects of 0.07 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.143, 0.0446] in score units. The design could detect effects of 0.08 SD or more; smaller leakage cannot be ruled out.

## construct: managerial_optimism
- **raw**: No detectable leakage: estimate +0.02 SD, 95% CI [-0.0639, 0.106] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate +0.03 SD, 95% CI [-0.053, 0.119] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate +0.02 SD, 95% CI [-0.0685, 0.106] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate +0.03 SD, 95% CI [-0.028, 0.108] in score units. The design could detect effects of 0.08 SD or more; smaller leakage cannot be ruled out.

## construct: risk_candour
- **raw**: No detectable leakage: estimate -0.05 SD, 95% CI [-0.125, 0.0196] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate -0.06 SD, 95% CI [-0.139, 0.0111] in score units. The design could detect effects of 0.11 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.106, 0.0355] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate -0.07 SD, 95% CI [-0.176, 0.00891] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.

## predict: all_outcomes
- **raw**: No detectable leakage: estimate -0.02 SD, 95% CI [-0.0191, 0.0113] in score units. The design could detect effects of 0.11 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.0202, 0.00859] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate +0.00 SD, 95% CI [-0.0127, 0.0141] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate -0.02 SD, 95% CI [-0.0155, 0.00812] in score units. The design could detect effects of 0.10 SD or more; smaller leakage cannot be ruled out.

## predict: bankruptcy
- **raw**: No detectable leakage: estimate +0.04 SD, 95% CI [-0.0273, 0.044] in score units. The design could detect effects of 0.22 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate +0.01 SD, 95% CI [-0.0287, 0.0352] in score units. The design could detect effects of 0.20 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate +0.01 SD, 95% CI [-0.0313, 0.038] in score units. The design could detect effects of 0.22 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate -0.08 SD, 95% CI [-0.0456, 0.0142] in score units. The design could detect effects of 0.21 SD or more; smaller leakage cannot be ruled out.

## predict: restatement
- **raw**: No detectable leakage: estimate -0.00 SD, 95% CI [-0.0102, 0.00964] in score units. The design could detect effects of 0.12 SD or more; smaller leakage cannot be ruled out.
- **names**: No detectable leakage: estimate -0.01 SD, 95% CI [-0.0108, 0.00936] in score units. The design could detect effects of 0.12 SD or more; smaller leakage cannot be ruled out.
- **generalised**: No detectable leakage: estimate +0.06 SD, 95% CI [-0.0016, 0.0167] in score units. The design could detect effects of 0.11 SD or more; smaller leakage cannot be ruled out.
- **paraphrased**: No detectable leakage: estimate +0.06 SD, 95% CI [-0.00157, 0.016] in score units. The design could detect effects of 0.11 SD or more; smaller leakage cannot be ruled out.

## Re-identification rate by masking level

| model         | level       |   hit |
|:--------------|:------------|------:|
| gpt4omini     | raw         |  0.72 |
| llama33       | raw         |  0.78 |
| haiku55       | raw         |  0.87 |
| gpt41mini     | raw         |  0.75 |
| llama4        | raw         |  0.78 |
| gemini25flash | raw         |  0.83 |
| gpt41mini     | names       |  0.49 |
| llama4        | names       |  0.54 |
| gpt4omini     | names       |  0.45 |
| gemini25flash | names       |  0.67 |
| llama33       | names       |  0.58 |
| haiku55       | names       |  0.73 |
| llama4        | generalised |  0.53 |
| llama33       | generalised |  0.57 |
| gemini25flash | generalised |  0.65 |
| haiku55       | generalised |  0.74 |
| gpt4omini     | generalised |  0.42 |
| gpt41mini     | generalised |  0.48 |
| gemini25flash | paraphrased |  0.10 |
| llama4        | paraphrased |  0.06 |
| llama33       | paraphrased |  0.06 |
| gpt4omini     | paraphrased |  0.02 |
| gpt41mini     | paraphrased |  0.05 |
| haiku55       | paraphrased |  0.13 |

## Leakage split by re-identification (pooled prediction)

| level       |   gamma_if_not_identified |   extra_gamma_if_identified |   se_extra |   p_extra |
|:------------|--------------------------:|----------------------------:|-----------:|----------:|
| generalised |                     0.003 |                      -0.004 |      0.008 |     0.595 |
| names       |                    -0.003 |                      -0.005 |      0.008 |     0.520 |
| paraphrased |                    -0.004 |                       0.010 |      0.009 |     0.274 |
| raw         |                    -0.003 |                      -0.001 |      0.008 |     0.940 |
