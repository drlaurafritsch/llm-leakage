# Robustness and power checks

## main

| spec                          | size   |   gamma_sd |   ci_low_sd |   ci_high_sd |   se_sd |   mde_sd |      p |   n_identifying |   size_sd |   size_se_sd |   size_p |
|:------------------------------|:-------|-----------:|------------:|-------------:|--------:|---------:|-------:|----------------:|----------:|-------------:|---------:|
| Prediction, bankruptcy        | no     |     0.0365 |     -0.1196 |       0.1927 |  0.0797 |   0.2231 | 0.6465 |             105 |  nan      |     nan      | nan      |
| Prediction, bankruptcy        | yes    |     0.0249 |     -0.137  |       0.1869 |  0.0826 |   0.2314 | 0.7629 |             105 |    0.0429 |       0.0767 |   0.5766 |
| Prediction, pooled            | no     |    -0.0197 |     -0.0967 |       0.0573 |  0.0393 |   0.11   | 0.6159 |             352 |  nan      |     nan      | nan      |
| Prediction, pooled            | yes    |    -0.0208 |     -0.0976 |       0.056  |  0.0392 |   0.1097 | 0.595  |             352 |   -0.0198 |       0.0263 |   0.4507 |
| Coding, distress (bankruptcy) | no     |    -0.0867 |     -0.172  |      -0.0015 |  0.0435 |   0.1218 | 0.0462 |             105 |  nan      |     nan      | nan      |
| Coding, distress (bankruptcy) | yes    |    -0.1042 |     -0.1936 |      -0.0149 |  0.0456 |   0.1277 | 0.0222 |             105 |    0.0757 |       0.0546 |   0.1657 |
| Coding, distress (pooled)     | no     |    -0.0026 |     -0.0525 |       0.0472 |  0.0254 |   0.0712 | 0.9181 |             343 |  nan      |     nan      | nan      |
| Coding, distress (pooled)     | yes    |    -0.0038 |     -0.0536 |       0.046  |  0.0254 |   0.0712 | 0.8809 |             343 |   -0.0196 |       0.019  |   0.304  |

## windows

| window               |   bankruptcy |   restatement |
|:---------------------|-------------:|--------------:|
| before all cutoffs   |           36 |           116 |
| Nov 2023 to Jan 2024 |           12 |            35 |
| Jan 2024 to Jun 2024 |           38 |            96 |
| Jun 2024 to Sep 2024 |           11 |            27 |
| Sep 2024 to Feb 2025 |           16 |            42 |
| Feb 2025 to Jul 2026 |           28 |            47 |
| after all cutoffs    |            1 |             0 |

## leave_one_out

| spec                          | dropped       |   gamma_sd |   ci_low_sd |   ci_high_sd |   se_sd |   mde_sd |      p |   n_identifying |   size_sd |   size_se_sd |   size_p |
|:------------------------------|:--------------|-----------:|------------:|-------------:|--------:|---------:|-------:|----------------:|----------:|-------------:|---------:|
| Prediction, bankruptcy        | none          |     0.0249 |     -0.137  |       0.1869 |  0.0826 |   0.2314 | 0.7629 |             105 |    0.0429 |       0.0767 |   0.5766 |
| Prediction, bankruptcy        | gemini25flash |     0.0256 |     -0.1668 |       0.2181 |  0.0982 |   0.2749 | 0.794  |             105 |    0.0493 |       0.093  |   0.5956 |
| Prediction, bankruptcy        | gpt41mini     |    -0.0026 |     -0.1782 |       0.173  |  0.0896 |   0.2508 | 0.977  |             105 |    0.0506 |       0.0753 |   0.5019 |
| Prediction, bankruptcy        | gpt4omini     |     0.0268 |     -0.1691 |       0.2227 |  0.1    |   0.2799 | 0.7885 |              92 |    0.1051 |       0.0912 |   0.249  |
| Prediction, bankruptcy        | haiku55       |    -0.0243 |     -0.209  |       0.1604 |  0.0942 |   0.2639 | 0.7966 |              77 |    0.0154 |       0.1019 |   0.8798 |
| Prediction, bankruptcy        | llama33       |     0.0716 |     -0.087  |       0.2303 |  0.0809 |   0.2266 | 0.3762 |             105 |    0.0398 |       0.0793 |   0.6156 |
| Prediction, bankruptcy        | llama4        |     0.0518 |     -0.1159 |       0.2194 |  0.0855 |   0.2395 | 0.545  |             105 |    0.0037 |       0.0825 |   0.9642 |
| Prediction, pooled            | none          |    -0.0208 |     -0.0976 |       0.056  |  0.0392 |   0.1097 | 0.595  |             352 |   -0.0198 |       0.0263 |   0.4507 |
| Prediction, pooled            | gemini25flash |    -0.0293 |     -0.1151 |       0.0565 |  0.0438 |   0.1226 | 0.5028 |             352 |   -0.0757 |       0.0292 |   0.0096 |
| Prediction, pooled            | gpt41mini     |    -0.0328 |     -0.1192 |       0.0537 |  0.0441 |   0.1235 | 0.4576 |             352 |   -0.0175 |       0.0286 |   0.5404 |
| Prediction, pooled            | gpt4omini     |    -0.0177 |     -0.1062 |       0.0707 |  0.0451 |   0.1263 | 0.6942 |             304 |   -0.0556 |       0.0335 |   0.0966 |
| Prediction, pooled            | haiku55       |    -0.0276 |     -0.1095 |       0.0542 |  0.0418 |   0.117  | 0.5081 |             277 |    0.1087 |       0.0255 |   0      |
| Prediction, pooled            | llama33       |    -0.0126 |     -0.0969 |       0.0717 |  0.043  |   0.1204 | 0.7696 |             352 |   -0.0329 |       0.0318 |   0.301  |
| Prediction, pooled            | llama4        |    -0.0039 |     -0.0796 |       0.0718 |  0.0386 |   0.1082 | 0.9197 |             352 |   -0.0385 |       0.0254 |   0.129  |
| Coding, distress (bankruptcy) | none          |    -0.1042 |     -0.1936 |      -0.0149 |  0.0456 |   0.1277 | 0.0222 |             105 |    0.0757 |       0.0546 |   0.1657 |
| Coding, distress (bankruptcy) | gemini25flash |    -0.126  |     -0.2282 |      -0.0239 |  0.0521 |   0.1459 | 0.0156 |             105 |    0.0727 |       0.0606 |   0.2302 |
| Coding, distress (bankruptcy) | gpt41mini     |    -0.1206 |     -0.2196 |      -0.0216 |  0.0505 |   0.1414 | 0.0169 |             105 |    0.0897 |       0.0563 |   0.1109 |
| Coding, distress (bankruptcy) | gpt4omini     |    -0.0941 |     -0.1938 |       0.0055 |  0.0509 |   0.1424 | 0.0642 |              93 |    0.0415 |       0.0625 |   0.5069 |
| Coding, distress (bankruptcy) | haiku55       |    -0.1098 |     -0.2113 |      -0.0083 |  0.0518 |   0.145  | 0.0339 |              77 |    0.0884 |       0.0569 |   0.12   |
| Coding, distress (bankruptcy) | llama33       |    -0.0749 |     -0.1721 |       0.0224 |  0.0496 |   0.1389 | 0.1313 |             105 |    0.0599 |       0.0676 |   0.3758 |
| Coding, distress (bankruptcy) | llama4        |    -0.1006 |     -0.1971 |      -0.0042 |  0.0492 |   0.1378 | 0.0409 |             105 |    0.0974 |       0.0582 |   0.0945 |
| Coding, distress (pooled)     | none          |    -0.0038 |     -0.0536 |       0.046  |  0.0254 |   0.0712 | 0.8809 |             343 |   -0.0196 |       0.019  |   0.304  |
| Coding, distress (pooled)     | gemini25flash |    -0.0028 |     -0.061  |       0.0555 |  0.0297 |   0.0832 | 0.9258 |             343 |   -0.0393 |       0.0231 |   0.089  |
| Coding, distress (pooled)     | gpt41mini     |     0.0035 |     -0.0538 |       0.0608 |  0.0292 |   0.0819 | 0.9051 |             343 |   -0.016  |       0.0208 |   0.4436 |
| Coding, distress (pooled)     | gpt4omini     |    -0.0339 |     -0.0875 |       0.0198 |  0.0274 |   0.0767 | 0.2163 |             296 |   -0.0051 |       0.02   |   0.7976 |
| Coding, distress (pooled)     | haiku55       |    -0.0006 |     -0.0523 |       0.051  |  0.0264 |   0.0738 | 0.9814 |             273 |   -0.0265 |       0.0211 |   0.2102 |
| Coding, distress (pooled)     | llama33       |     0.0085 |     -0.0488 |       0.0659 |  0.0293 |   0.0819 | 0.771  |             343 |   -0.0205 |       0.0219 |   0.3484 |
| Coding, distress (pooled)     | llama4        |     0.0003 |     -0.0553 |       0.0559 |  0.0284 |   0.0794 | 0.9914 |             343 |   -0.0109 |       0.0194 |   0.5733 |

## horizon

| spec                          |   gamma_sd |   ci_low_sd |   ci_high_sd |      p |
|:------------------------------|-----------:|------------:|-------------:|-------:|
| Prediction, bankruptcy        |     0.0632 |     -0.0913 |       0.2176 | 0.4228 |
| Prediction, pooled            |    -0.0018 |     -0.084  |       0.0804 | 0.9659 |
| Coding, distress (bankruptcy) |    -0.059  |     -0.1483 |       0.0302 | 0.1947 |
| Coding, distress (pooled)     |     0.0294 |     -0.0222 |       0.081  | 0.2643 |

## placebo

| spec                          |   gamma_sd |   ci_low_sd |   ci_high_sd |   se_sd |   mde_sd |      p |   n_identifying |
|:------------------------------|-----------:|------------:|-------------:|--------:|---------:|-------:|----------------:|
| Prediction, bankruptcy        |    -0.0103 |     -0.1351 |       0.1145 |  0.0637 |   0.1783 | 0.8714 |             105 |
| Prediction, pooled            |    -0.0051 |     -0.0462 |       0.0361 |  0.021  |   0.0588 | 0.8099 |             692 |
| Coding, distress (bankruptcy) |    -0.091  |     -0.1885 |       0.0065 |  0.0497 |   0.1393 | 0.0674 |             105 |
| Coding, distress (pooled)     |    -0.0248 |     -0.0768 |       0.0272 |  0.0265 |   0.0743 | 0.3504 |             343 |

## model_size

| spec                          | sample   | controls     |   gamma_sd |   ci_low_sd |   ci_high_sd |      p |   size_sd |   size_se_sd |   size_p |
|:------------------------------|:---------|:-------------|-----------:|------------:|-------------:|-------:|----------:|-------------:|---------:|
| Prediction, bankruptcy        | real     | no           |    -0.0546 |     -0.2352 |       0.1259 | 0.5531 |    0.1749 |       0.0918 |   0.0568 |
| Prediction, bankruptcy        | real     | model x size |     0.0249 |     -0.137  |       0.1869 | 0.7629 |    0.0429 |       0.0767 |   0.5766 |
| Prediction, bankruptcy        | placebo  | no           |    -0.0552 |     -0.1849 |       0.0744 | 0.4035 |    0.1343 |       0.0569 |   0.0182 |
| Prediction, bankruptcy        | placebo  | model x size |    -0.0062 |     -0.1262 |       0.1137 | 0.9188 |    0.0597 |       0.0571 |   0.2961 |
| Prediction, pooled            | real     | no           |    -0.0216 |     -0.0979 |       0.0546 | 0.5785 |    0.0718 |       0.0218 |   0.001  |
| Prediction, pooled            | real     | model x size |    -0.0208 |     -0.0976 |       0.056  | 0.595  |   -0.0198 |       0.0263 |   0.4507 |
| Prediction, pooled            | placebo  | no           |    -0.0092 |     -0.0537 |       0.0354 | 0.6863 |    0.0984 |       0.0177 |   0      |
| Prediction, pooled            | placebo  | model x size |    -0.0051 |     -0.0461 |       0.0359 | 0.8068 |   -0.0035 |       0.0194 |   0.8575 |
| Coding, distress (bankruptcy) | real     | no           |    -0.0803 |     -0.1669 |       0.0063 | 0.069  |   -0.0033 |       0.0544 |   0.9522 |
| Coding, distress (bankruptcy) | real     | model x size |    -0.1042 |     -0.1936 |      -0.0149 | 0.0222 |    0.0757 |       0.0546 |   0.1657 |
| Coding, distress (bankruptcy) | placebo  | no           |    -0.0962 |     -0.1946 |       0.0021 | 0.0552 |   -0.1216 |       0.0482 |   0.0117 |
| Coding, distress (bankruptcy) | placebo  | model x size |    -0.0953 |     -0.1922 |       0.0016 | 0.0538 |   -0.0657 |       0.0497 |   0.1861 |
| Coding, distress (pooled)     | real     | no           |    -0.0038 |     -0.0531 |       0.0455 | 0.881  |   -0.0986 |       0.0179 |   0      |
| Coding, distress (pooled)     | real     | model x size |    -0.0038 |     -0.0536 |       0.046  | 0.8809 |   -0.0196 |       0.019  |   0.304  |
| Coding, distress (pooled)     | placebo  | no           |    -0.0221 |     -0.0752 |       0.0309 | 0.4135 |   -0.1098 |       0.0174 |   0      |
| Coding, distress (pooled)     | placebo  | model x size |    -0.0251 |     -0.0772 |       0.0269 | 0.3444 |   -0.016  |       0.0188 |   0.3954 |

## stacked

| spec                          |   gamma_sd |   ci_low_sd |   ci_high_sd |      p |   windows_used |   identifying_events |
|:------------------------------|-----------:|------------:|-------------:|-------:|---------------:|---------------------:|
| Prediction, bankruptcy        |    -0.0115 |     -0.2081 |       0.1851 | 0.9089 |              4 |                   77 |
| Prediction, pooled            |    -0.0525 |     -0.1458 |       0.0408 | 0.2701 |              4 |                  277 |
| Coding, distress (bankruptcy) |    -0.0243 |     -0.1347 |       0.086  | 0.6654 |              4 |                   77 |
| Coding, distress (pooled)     |     0.0007 |     -0.059  |       0.0605 | 0.9806 |              4 |                  273 |

## stacked_windows

| spec                          | treated_model   | window               |   events_in_window |   later_events | used   |   gamma_sd |    se_sd |        p |
|:------------------------------|:----------------|:---------------------|-------------------:|---------------:|:-------|-----------:|---------:|---------:|
| Prediction, bankruptcy        | llama33         | Nov 2023 to Jan 2024 |                 12 |             94 | True   |    -0.5855 |   0.182  |   0.0013 |
| Prediction, bankruptcy        | gpt41mini       | Jan 2024 to Jun 2024 |                 38 |             56 | True   |     0.2172 |   0.1247 |   0.0816 |
| Prediction, bankruptcy        | llama4          | Jun 2024 to Sep 2024 |                 11 |             45 | True   |    -0.1055 |   0.2792 |   0.7055 |
| Prediction, bankruptcy        | gemini25flash   | Sep 2024 to Feb 2025 |                 16 |             29 | True   |     0.0173 |   0.1239 |   0.8893 |
| Prediction, bankruptcy        | haiku55         | Feb 2025 to Jul 2026 |                 28 |              1 | False  |   nan      | nan      | nan      |
| Prediction, pooled            | llama33         | Nov 2023 to Jan 2024 |                 47 |            306 | True   |    -0.2466 |   0.1095 |   0.0243 |
| Prediction, pooled            | gpt41mini       | Jan 2024 to Jun 2024 |                134 |            172 | True   |     0.0526 |   0.0597 |   0.3784 |
| Prediction, pooled            | llama4          | Jun 2024 to Sep 2024 |                 38 |            134 | True   |    -0.198  |   0.1343 |   0.1404 |
| Prediction, pooled            | gemini25flash   | Sep 2024 to Feb 2025 |                 58 |             76 | True   |     0.0201 |   0.0668 |   0.7632 |
| Prediction, pooled            | haiku55         | Feb 2025 to Jul 2026 |                 75 |              1 | False  |   nan      | nan      | nan      |
| Coding, distress (bankruptcy) | llama33         | Nov 2023 to Jan 2024 |                 12 |             94 | True   |    -0.119  |   0.0882 |   0.177  |
| Coding, distress (bankruptcy) | gpt41mini       | Jan 2024 to Jun 2024 |                 38 |             56 | True   |     0.0122 |   0.0718 |   0.8646 |
| Coding, distress (bankruptcy) | llama4          | Jun 2024 to Sep 2024 |                 11 |             45 | True   |    -0.2068 |   0.1593 |   0.1942 |
| Coding, distress (bankruptcy) | gemini25flash   | Sep 2024 to Feb 2025 |                 16 |             29 | True   |     0.1164 |   0.1307 |   0.3732 |
| Coding, distress (bankruptcy) | haiku55         | Feb 2025 to Jul 2026 |                 28 |              1 | False  |   nan      | nan      | nan      |
| Coding, distress (pooled)     | llama33         | Nov 2023 to Jan 2024 |                 47 |            297 | True   |    -0.0076 |   0.0857 |   0.9296 |
| Coding, distress (pooled)     | gpt41mini       | Jan 2024 to Jun 2024 |                131 |            166 | True   |     0.0181 |   0.0416 |   0.6634 |
| Coding, distress (pooled)     | llama4          | Jun 2024 to Sep 2024 |                 38 |            128 | True   |    -0.0496 |   0.0723 |   0.4924 |
| Coding, distress (pooled)     | gemini25flash   | Sep 2024 to Feb 2025 |                 57 |             71 | True   |     0.0177 |   0.0803 |   0.8259 |
| Coding, distress (pooled)     | haiku55         | Feb 2025 to Jul 2026 |                 70 |              1 | False  |   nan      | nan      | nan      |

## donut

| spec                          |   donut_days |   gamma_sd |   ci_low_sd |   ci_high_sd |   se_sd |   mde_sd |      p |   n_identifying |
|:------------------------------|-------------:|-----------:|------------:|-------------:|--------:|---------:|-------:|----------------:|
| Prediction, bankruptcy        |          182 |     0.1733 |     -0.088  |       0.4346 |  0.1333 |   0.3733 | 0.1936 |              56 |
| Prediction, pooled            |          182 |     0.0508 |     -0.0763 |       0.1778 |  0.0648 |   0.1815 | 0.4336 |             186 |
| Coding, distress (bankruptcy) |          182 |    -0.1066 |     -0.3012 |       0.088  |  0.0993 |   0.2781 | 0.2831 |              56 |
| Coding, distress (pooled)     |          182 |    -0.0027 |     -0.1078 |       0.1025 |  0.0536 |   0.1502 | 0.9606 |             180 |
| Prediction, bankruptcy        |          365 |     0.1568 |     -0.2553 |       0.569  |  0.2103 |   0.5888 | 0.4557 |              21 |
| Prediction, pooled            |          365 |     0.0925 |     -0.0844 |       0.2693 |  0.0902 |   0.2526 | 0.3054 |              76 |
| Coding, distress (bankruptcy) |          365 |     0.0612 |     -0.2458 |       0.3683 |  0.1567 |   0.4387 | 0.6958 |              21 |
| Coding, distress (pooled)     |          365 |     0.0032 |     -0.1587 |       0.1651 |  0.0826 |   0.2313 | 0.9694 |              72 |

## knows_checks

| task       | check                               |    coef |     se |      p |   coef_sd |   n_yes |   ci_low |   ci_high |
|:-----------|:------------------------------------|--------:|-------:|-------:|----------:|--------:|---------:|----------:|
| prediction | falsification: yes_knowable         |  2.8935 | 1.7021 | 0.0891 |    0.1269 |     198 | nan      |  nan      |
| prediction | falsification: yes_unknowable_event | -5.3035 | 7.0337 | 0.4508 |   -0.2325 |      15 | nan      |  nan      |
| prediction | falsification: yes_control          |  2.2263 | 1.1019 | 0.0433 |    0.0976 |     193 | nan      |  nan      |
| prediction | without Llama 4 Maverick            |  3.7105 | 2.0714 | 0.0732 |    0.1722 |     nan | nan      |  nan      |
| prediction | re-identification split: kk         |  0.8219 | 3.817  | 0.8295 |    0.036  |     nan | nan      |  nan      |
| prediction | re-identification split: kk_hit     |  2.3798 | 4.0282 | 0.5547 |    0.1043 |     nan | nan      |  nan      |
| prediction | re-identification split: know_hit   |  0.183  | 2.0435 | 0.9286 |    0.008  |     nan | nan      |  nan      |
| prediction | raw minus paraphrased (bootstrap)   |  3.4768 | 1.6151 | 0.0533 |  nan      |     nan |   0.0045 |    6.5359 |
| coding     | falsification: yes_knowable         |  0.0217 | 0.0805 | 0.7872 |    0.0122 |     198 | nan      |  nan      |
| coding     | falsification: yes_unknowable_event |  0.2413 | 0.1552 | 0.1199 |    0.1351 |      15 | nan      |  nan      |
| coding     | falsification: yes_control          | -0.0011 | 0.056  | 0.985  |   -0.0006 |     144 | nan      |  nan      |
| coding     | without Llama 4 Maverick            |  0.0128 | 0.0869 | 0.8832 |    0.007  |     nan | nan      |  nan      |
| coding     | re-identification split: kk         | -0.5705 | 0.2459 | 0.0203 |   -0.3194 |     nan | nan      |  nan      |
| coding     | re-identification split: kk_hit     |  0.6339 | 0.247  | 0.0103 |    0.3549 |     nan | nan      |  nan      |
| coding     | re-identification split: know_hit   | -0.1013 | 0.1498 | 0.4988 |   -0.0567 |     nan | nan      |  nan      |
| coding     | raw minus paraphrased (bootstrap)   |  0.0221 | 0.0876 | 0.9467 |  nan      |     nan |  -0.1616 |    0.1574 |

## permutation

| spec                          |   gamma_sd |   n_perms |   p_two_sided |   perm_q025 |   perm_q975 |
|:------------------------------|-----------:|----------:|--------------:|------------:|------------:|
| Prediction, bankruptcy        |     0.0365 |       720 |        0.7083 |     -0.1602 |      0.1696 |
| Prediction, pooled            |    -0.0197 |       720 |        0.5736 |     -0.0567 |      0.0565 |
| Coding, distress (bankruptcy) |    -0.0867 |       720 |        0.1194 |     -0.1044 |      0.114  |
| Coding, distress (pooled)     |    -0.0026 |       720 |        0.9264 |     -0.0449 |      0.0538 |

## first_stage

| measure     | model         |   n_control |   n_event, after cutoff |   n_event, knowable |   says_yes_control |   says_yes_event, after cutoff |   says_yes_event, knowable |
|:------------|:--------------|------------:|------------------------:|--------------------:|-------------------:|-------------------------------:|---------------------------:|
| bankruptcy  | gemini25flash |        1331 |                      29 |                 113 |             0.0173 |                         0      |                     0.4336 |
| bankruptcy  | gpt41mini     |        1331 |                      56 |                  86 |             0.0008 |                         0      |                     0.1279 |
| bankruptcy  | gpt4omini     |        1331 |                     106 |                  36 |             0.003  |                         0.0189 |                     0.25   |
| bankruptcy  | haiku55       |        1331 |                       1 |                 141 |             0.0158 |                         1      |                     0.461  |
| bankruptcy  | llama33       |        1331 |                      94 |                  48 |             0.0218 |                         0.0532 |                     0.3333 |
| bankruptcy  | llama4        |        1331 |                      45 |                  97 |             0.0872 |                         0.1556 |                     0.4948 |
| restatement | gemini25flash |        1110 |                      47 |                 316 |             0.0279 |                         0.0213 |                     0.0886 |
| restatement | gpt41mini     |        1110 |                     116 |                 247 |             0.0018 |                         0      |                     0      |
| restatement | gpt4omini     |        1110 |                     247 |                 116 |             0      |                         0      |                     0.0172 |
| restatement | haiku55       |        1110 |                     nan |                 363 |             0.0099 |                       nan      |                     0.0413 |
| restatement | llama33       |        1110 |                     212 |                 151 |             0      |                         0      |                     0.0265 |
| restatement | llama4        |        1110 |                      89 |                 274 |             0.0306 |                         0.0225 |                     0.0584 |

## knows_diff

|   lambda_prediction_sd |   se_prediction |   lambda_coding_sd |   se_coding |   difference_sd |   se_difference |   ci_low |   ci_high |   p_difference |   boot_reps |
|-----------------------:|----------------:|-------------------:|------------:|----------------:|----------------:|---------:|----------:|---------------:|------------:|
|                 0.1329 |          0.0827 |             0.0086 |       0.044 |          0.1243 |          0.0773 |  -0.0272 |    0.2758 |         0.0867 |         300 |

## signal

| task      | measure             |   generalised |   names |   paraphrased |    raw |
|:----------|:--------------------|--------------:|--------:|--------------:|-------:|
| construct | financial_distress  |        0.5385 |  0.5422 |        0.5374 | 0.5475 |
| construct | managerial_optimism |        0.508  |  0.4965 |        0.4777 | 0.4962 |
| construct | risk_candour        |        0.518  |  0.5156 |        0.5118 | 0.5175 |
| predict   | bankruptcy          |        0.4977 |  0.5216 |        0.5169 | 0.5228 |
| predict   | restatement         |        0.4977 |  0.5092 |        0.5174 | 0.5053 |
