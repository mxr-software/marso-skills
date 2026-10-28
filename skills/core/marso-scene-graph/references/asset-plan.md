# How unique assets are derived

`plan_assets.py` applies these rules. Read this to check its output or to adjust a plan by hand.

## From nodes to assets

| In the graph | In the plan |
| --- | --- |
| A node with `parent: null` | An anchor, listed under `anchors`, never an asset. |
| A node marked `unconfirmed` | Listed under `unconfirmed`, never an asset. A wide view named it with low confidence inside the region a close-up covers, and the close-up never matched it: it is probably one of the close-up's objects misread. Review it; make it an asset only if the user confirms it is a separate thing. |
| A cluster of kind `instances` | One asset. Its `members` are the cluster's members, `count` is how many physical things they are. The graph names a cluster `cl_id`. |
| A cluster of kind `variants` | One asset per member. Each carries the shared `cluster_id` so the family stays visible. |
| Nodes in an identity group that are in no `instances` cluster | One asset whose count comes from the group. |
| Any other node | One asset with count 1. |

An `instances` cluster and an identity group that share a member are one asset: four onions in a bowl in one photograph and an onion in another that may be one of them are 4 to 5 onions, not 4 + 1. A node is never in two assets.

## Counting with identity groups

Unconfirmed members are left out before counting, and the group's floor and ceiling are clipped to the members that remain; the asset is flagged `identity-group-has-unconfirmed`.

An identity group says that several nodes stand for fewer physical objects: the match stage could not tell whether a close-up showed the same chair as a wide shot. For each asset:

- `count_at_most` is the number of members.
- `count_at_least` subtracts, for each identity group fully inside the asset, the difference between the group's `at_most` and `at_least`.
- `count` uses the group's `distinct` where it is given, otherwise `count_at_least`.

When a group is split across two assets, the script keeps each side's members and adds the flag `identity-group-split`. That is a graph problem to resolve before trusting the count.

Never narrow the range by guessing. Report "2 to 3 chairs" to the user and ask, or go back to the images.

## Children and parents

Each asset records its `parent` and `relation` from the representative node, and `children` as every node whose parent is one of its members. Children are what the crop masks by default; the parent is what `--exclude-parent` masks. Nodes with relation `part-of` are not separate assets by default: they are skipped and named in the parent's `children` so the parent's brief mentions them.

## Order and identifiers

Assets are numbered `a001`, `a002`, ... in order of their first member's `global_id`. The identifier is stable for a given graph and plan run; re-running with `--force` on an unchanged graph gives the same ids. Edit the plan by hand freely, but keep `members` as `global_id`s so the crop step can find the boxes.
