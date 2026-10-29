# Leakage report

## construct: financial_distress
- **raw**: No detectable leakage: estimate -0.00 SD, 95% CI [-0.0945, 0.081] in score units.
- **names**: No detectable leakage: estimate +0.00 SD, 95% CI [-0.0848, 0.0982] in score units.
- **generalised**: No detectable leakage: estimate +0.01 SD, 95% CI [-0.0664, 0.11] in score units.
- **paraphrased**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.143, 0.0443] in score units.

## construct: managerial_optimism
- **raw**: No detectable leakage: estimate +0.02 SD, 95% CI [-0.0535, 0.114] in score units.
- **names**: No detectable leakage: estimate +0.03 SD, 95% CI [-0.0425, 0.128] in score units.
- **generalised**: No detectable leakage: estimate +0.02 SD, 95% CI [-0.0597, 0.114] in score units.
- **paraphrased**: No detectable leakage: estimate +0.04 SD, 95% CI [-0.0257, 0.11] in score units.

## construct: risk_candour
- **raw**: No detectable leakage: estimate -0.05 SD, 95% CI [-0.126, 0.0241] in score units.
- **names**: No detectable leakage: estimate -0.06 SD, 95% CI [-0.136, 0.0175] in score units.
- **generalised**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.106, 0.0396] in score units.
- **paraphrased**: No detectable leakage: estimate -0.06 SD, 95% CI [-0.172, 0.0172] in score units.

## predict: all_outcomes
- **raw**: No detectable leakage: estimate -0.02 SD, 95% CI [-0.0193, 0.0108] in score units.
- **names**: No detectable leakage: estimate -0.03 SD, 95% CI [-0.0206, 0.00796] in score units.
- **generalised**: No detectable leakage: estimate +0.00 SD, 95% CI [-0.0125, 0.0136] in score units.
- **paraphrased**: No detectable leakage: estimate -0.02 SD, 95% CI [-0.0152, 0.00816] in score units.

## predict: bankruptcy
- **raw**: No detectable leakage: estimate -0.05 SD, 95% CI [-0.0536, 0.0287] in score units.
- **names**: No detectable leakage: estimate -0.07 SD, 95% CI [-0.0525, 0.0212] in score units.
- **generalised**: No detectable leakage: estimate -0.05 SD, 95% CI [-0.0478, 0.027] in score units.
- **paraphrased**: No detectable leakage: estimate -0.12 SD, 95% CI [-0.057, 0.0097] in score units.

## predict: restatement
- **raw**: No detectable leakage: estimate +0.00 SD, 95% CI [-0.00964, 0.00973] in score units.
- **names**: No detectable leakage: estimate -0.01 SD, 95% CI [-0.0105, 0.0092] in score units.
- **generalised**: No detectable leakage: estimate +0.07 SD, 95% CI [-0.001, 0.017] in score units.
- **paraphrased**: No detectable leakage: estimate +0.07 SD, 95% CI [-0.000962, 0.0166] in score units.

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
| generalised |                     0.000 |                      -0.001 |      0.008 |     0.895 |
| names       |                    -0.008 |                       0.001 |      0.008 |     0.874 |
| paraphrased |                    -0.005 |                       0.015 |      0.009 |     0.082 |
| raw         |                    -0.011 |                       0.007 |      0.008 |     0.404 |
