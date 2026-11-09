# ModuleTwo hardware validation

Follow-up to [issue #5](https://github.com/tjorim/python-mygrid-modbus/issues/5).

## 2026-11-09 read-only check

The user supplied a ModuleTwo endpoint on the local LAN, port 502, and subsequently reported **Software 31.6** for this replacement battery. The software version was supplied by the owner, not read over Modbus. No setpoint or restart commands were sent.

```sh
MYGRID_HOST=<battery> MYGRID_PORT=502 uv run pytest -m live
# 2 passed, 70 deselected in 0.59s
uv run script/query.py <battery> --port 502 --raw
```

Both live smoke tests passed: a validated snapshot was internally consistent, the raw response contained holding registers 0–17, register 0 reported map version 2, and restart register 9 read zero. A subsequent CLI query also succeeded:

| Reading | Value |
| --- | --- |
| Map version | 2 |
| State of charge | 49% |
| Status / fault flags | 0 (normal) / 0 |
| Setpoint / measured power | 0 W / 0 W |
| Maximum charge / discharge | 1200 W / 800 W |
| Stored energy / total capacity | 2000 Wh / 3978 Wh |
| Lifetime charged / discharged | 1446 Wh / 111 Wh |

The CLI returned holding registers 0–17 in address order:

```text
[2, 49, 0, 12, 8, 0, 0, 0, 0, 0, 2000, 0, 1446, 0, 111, 0, 3978, 0]
```

No discrepancy requiring a protocol correction was observed. These observations cover this unit at this time. Zero power and zero high words do not independently establish signed-power behavior or U32 word order; those remain covered by the manual and offline tests. Writes, restart, stale/fault states and cluster behavior were not exercised.

## Activation history reported by the owner

After the successful tests, the owner clarified that the previous battery had been broken and replaced. The replacement started updating once linked to the owner's MyGrid account. The owner then enabled Home Assistant control again (normally used via MQTT), after which Modbus TCP was available.

This resolves the reported access problem on the replacement unit and is consistent with the manual's Home Assistant control setting. The earlier refusal belongs to the previous battery; it is not evidence that the replacement required a separate IT activation. The report does not establish what changed internally or whether the earlier fault had the same cause.

## Read-only device-identification probe

A single standard Read Device Identification request (function 43 / MEI 14, basic access, starting object 0) was sent to unit 1 on the replacement battery. The response PDU was `ab 01`: exception function `0xAB`, exception code 1 (Illegal Function). This unit rejected the standard device-identification request, so it supplied no manufacturer, model or firmware revision through that request. No undocumented registers were scanned and no writes were sent.

## Network discovery observations

A bounded read-only scan of the local /24 subnet found two endpoints returning identical valid map-2 snapshots, including capacity and lifetime energy counters. Their MAC addresses were closely related, consistent with two interfaces to the same battery, but the documented map provides no unique identity to confirm that association or distinguish Ethernet from Wi-Fi.

An mDNS check observed a Voltbridge P1 meter advertising `_mygrid._tcp`, with model, device ID and firmware metadata. No equivalent battery advertisement was observed during the bounded check. A future discovery implementation must distinguish the meter from a ModuleTwo; these observations do not add discovery support to the library.

## Remaining verification limits

- Software version: **31.6**, reported by the owner; the documented map has no firmware-version register.
- Account linking and selecting Home Assistant control made Modbus available on the replacement, as reported by the owner. Any internal IT changes or wider activation scope remain unknown.
- Persistence across restart/update and dependence on cloud connectivity: untested.
- Competing clients being disconnected: not confirmed by the user.
- Hub known-issue documentation and HACS hardware acceptance follow-up: still need to reflect this limited read-only result in their respective repositories.

The earlier connection refusal on 2026-10-24 remains historical evidence for the previous unit. Local MQTT was not investigated because Modbus reads succeeded. The access problem is resolved on the replacement; persistence and cloud independence remain unverified.
