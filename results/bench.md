## 30 recorded claim runs

| Claim | Planted problems | Node path | Status | Decision | Tokens | Cost |
|---|---|---|---|---|---|---|
| CLM-0000 | duplicate_claim | extractor → investigator → reviewer → extractor → investigator → reviewer → recommend | decided | refer | 3,359 | $0.00062 |
| CLM-0001 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 556.28 | 1,946 | $0.00036 |
| CLM-0002 | lapsed_policy | extractor → investigator → reviewer → investigator → reviewer → recommend | decided | deny | 2,927 | $0.00053 |
| CLM-0003 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,374.57 | 1,980 | $0.00036 |
| CLM-0004 | — | extractor → investigator → reviewer → extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,564.59 | 3,522 | $0.00066 |
| CLM-0005 | lapsed_policy | extractor → investigator → reviewer → recommend | decided | deny | 1,948 | $0.00036 |
| CLM-0006 | — | extractor → investigator → reviewer → extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,317.61 | 3,543 | $0.00067 |
| CLM-0007 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,161.49 | 1,983 | $0.00036 |
| CLM-0008 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,005.89 | 1,982 | $0.00036 |
| CLM-0009 | — | extractor → investigator → reviewer → extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,488.02 | 3,409 | $0.00063 |
| CLM-0010 | duplicate_claim, missing_estimate | extractor → investigator → reviewer → recommend | decided | refer | 1,868 | $0.00034 |
| CLM-0011 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 785.12 | 1,947 | $0.00036 |
| CLM-0012 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,489.89 | 2,009 | $0.00037 |
| CLM-0013 | duplicate_claim | extractor → investigator → reviewer → recommend | decided | refer | 1,973 | $0.00036 |
| CLM-0014 | duplicate_claim, over_limit | extractor → investigator → reviewer → recommend | decided | refer | 1,946 | $0.00036 |
| CLM-0015 | duplicate_claim, over_limit | extractor → investigator → reviewer → recommend | decided | refer | 1,915 | $0.00035 |
| CLM-0016 | — | extractor → investigator → reviewer → extractor → investigator → reviewer → investigator → reviewer | stopped_review_loop | — | 3,811 | $0.00071 |
| CLM-0017 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 1,049.65 | 1,943 | $0.00036 |
| CLM-0018 | missing_estimate | extractor → investigator → reviewer → recommend | decided | refer | 1,862 | $0.00034 |
| CLM-0019 | duplicate_claim, missing_estimate | extractor → investigator → reviewer → recommend | decided | refer | 1,865 | $0.00034 |
| CLM-0020 | inflated_estimate | extractor → investigator → reviewer → extractor → investigator → reviewer → recommend | decided | refer | 3,551 | $0.00069 |
| CLM-0021 | over_limit | extractor → investigator → reviewer → recommend | awaiting_approval | approve 300.00 | 1,985 | $0.00037 |
| CLM-0022 | missing_estimate | extractor → investigator → reviewer → recommend | decided | refer | 1,867 | $0.00034 |
| CLM-0023 | missing_estimate | extractor → investigator → reviewer → recommend | decided | refer | 1,864 | $0.00034 |
| CLM-0024 | — | extractor → investigator → reviewer → investigator → reviewer → recommend | awaiting_approval | approve 1,693.77 | 2,966 | $0.00054 |
| CLM-0025 | — | extractor → investigator → reviewer → recommend | awaiting_approval | approve 608.37 | 1,942 | $0.00035 |
| CLM-0026 | — | extractor → investigator → reviewer → investigator → reviewer → recommend | awaiting_approval | approve 989.38 | 2,920 | $0.00053 |
| CLM-0027 | lapsed_policy | extractor → investigator → reviewer → recommend | decided | deny | 2,021 | $0.00038 |
| CLM-0028 | missing_estimate, over_limit | extractor → investigator → reviewer → investigator → reviewer → recommend | decided | refer | 2,779 | $0.00050 |
| CLM-0029 | — | extractor → investigator → reviewer → investigator → reviewer → recommend | awaiting_approval | approve 1,181.24 | 2,875 | $0.00052 |

## Ship gates

- Replay: CLM-0000 resumed from its step-3 snapshot reached the same terminal state (fingerprint 3bc0dfcb3ab02a42 vs 3bc0dfcb3ab02a42): **True**.
- Send-backs: 290 of 900 claims were sent back by the reviewer at least once (232 once, 58 twice); every claim stopped, the longest after 9 node runs (limit 10).
- Stops: {'decided': 370, 'awaiting_approval': 518, 'stopped_review_loop': 12}.
- Cost per claim (ceiling $0.002): median $0.00037, max $0.00084.
- With the ceiling cut to $0.0006: 218 claims stopped before the call that would cross it; the most any claim spent was $0.00056.
- Human gate: 518 payouts waited for approval and none paid without one; approving CLM-0001 moved it to `paid`.

Cost per claim, 900 claims:

```
$0.00034-0.00040 ################################################## 579
$0.00040-0.00046 ###                                                31
$0.00046-0.00052 ######                                             69
$0.00052-0.00059 #####                                              56
$0.00059-0.00065 #####                                              61
$0.00065-0.00071 ######                                             74
$0.00071-0.00077 #                                                  8
$0.00077-0.00084 ##                                                 22
```

## Planted problems caught (900 claims)

| Problem | Planted | Caught | False flags on other claims |
|---|---|---|---|
| over_limit | 98 | 87 (89%) | 0 |
| lapsed_policy | 105 | 105 (100%) | 0 |
| inflated_estimate | 107 | 95 (89%) | 0 |
| duplicate_claim | 127 | 125 (98%) | 0 |
| missing_estimate | 105 | 105 (100%) | 0 |
