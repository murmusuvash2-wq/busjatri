#!/usr/bin/env python3
"""Apply approved user reports (report system Phase B).

Reads data/time-reports.json (synced from the Google Sheet by
scripts/fetch_time_reports.py). Rows whose Status is 'approved':

  * type 'add-time'  -> merged into data/time-overrides.json, so the
    approved stop time shows on the live site instantly (runtime patch;
    apply_time_overrides.py folds them into the source data on rebuilds)
  * any approved row with a non-empty Name -> counted in
    data/contributors.json for the footer credit line

Rejected/blank rows are ignored. Applied rows keep their 'approved'
status so they are never applied twice (merge is idempotent anyway).
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / 'data' / 'time-reports.json'
OVR = ROOT / 'data' / 'time-overrides.json'
CON = ROOT / 'data' / 'contributors.json'


def norm_time(t):
    """'9:5 AM' / '09:05 am' -> '9:05 AM'; None if unparseable."""
    m = re.match(r'^\s*(\d{1,2}):ÌŸJWÊŠS_JWÊ‰	ËÝŠÜˆ	ÉÊKœÝš\

K\\Š
JBˆYˆ›ÝN‚ˆ™]\›ˆ›Û™BˆZK\H[
K™Ü›Ý\
JJKK™Ü›Ý\
ŠKK™Ü›Ý\
ÊBˆYˆ\OH	ÔIÈ[™OHLŽ‚ˆ
ÏHL‚ˆYˆ\OH	ÐSIÈ[™OHLŽ‚ˆHˆYˆˆŒÎ‚ˆ™]\›ˆ›Û™BˆLˆH	HLˆÜˆL‚ˆ™]\›ˆˆžÚLŸNžÛZ_HÉÔIÈYˆHLˆ[ÙH	ÐSIßH‚‚‚™YˆÛX[—Û˜[YJŠN‚ˆˆH™KœÝXŠ‰ÖÏ‰ˆ—IË	ÉËÝŠˆÜˆ	ÉÊJKœÝš\

Bˆ™]\›ˆ–ÎŒÌB‚‚™YˆXZ[Š
N‚ˆ™\ÜÈHœÛÛ‹›ØYÊ‘Tœ™XYÝ^
[˜ÛÙ[™ÏIÝ]‹N	ÊJHYˆ‘T™^\ÝÊ
H[ÙH×BˆÝˆHœÛÛ‹›ØYÊÕ”‹œ™XYÝ^
[˜ÛÙ[™ÏIÝ]‹N	ÊJHYˆÕ”‹™^\ÝÊ
H[ÙHßB‚ˆ—Ø\YYHˆÚÚ\YH×Bˆ›Üˆˆ[ˆ™\ÜÎ‚ˆYˆ
‹™Ù]
	ÜÝ]\ÉÊHÜˆ	ÉÊKœÝš\

K›ÝÙ\Š
HOH	Ø\›Ý™Y	Î‚ˆÛÛ[YBˆYˆ
‹™Ù]
	Ý\IÊHÜˆ	Ý[YK\™\Ü	ÊKœÝš\

HOH	ØY][YIÎ‚ˆÛÛ[YHÈ\Ë\ÝÜYÈ›Ý]KXÚ[™ÙHÈ\Ë[]™[[YH™\ÜÈÝ^H™]šY]Ë[Û›BˆšYH
‹™Ù]
	Ø\×ÚY	ÊHÜˆ	ÉÊKœÝš\

BˆÝÜH
‹™Ù]
	ÜÝÜ	ÊHÜˆ	ÉÊKœÝš\

BˆH›Ü›WÝ[YJ‹™Ù]
	Ý[YIÊJBˆYˆ›Ý
šY[™ÝÜ[™
N‚ˆÚÚ\Y˜\[™
ŠBˆÛÛ[YBˆH	ÙÝÛ‰ÈYˆ
‹™Ù]
	Ù\‰ÊHÜˆ	ÉÊKœÝš\

K›ÝÙ\Š
KœÝ\ÝÚ]
	Ù	ÊH[ÙH	Ý\	ÂˆÝ‹œÙ]Y˜][
šYßJKœÙ]Y˜][
ÝÜßJVÙHHˆ—Ø\YY
ÏHB‚ˆÕ”‹Üš]WÝ^
œÛÛ‹™[\ÊÝ‹[œÝ\™WØ\ØÚZOQ˜[ÙK[™[LJK[˜ÛÙ[™ÏIÝ]‹N	ÊB‚ˆÛÝ[ÈHÛÝ[\Š
Bˆ›Üˆˆ[ˆ™\ÜÎ‚ˆYˆ
‹™Ù]
	ÜÝ]\ÉÊHÜˆ	ÉÊKœÝš\

K›ÝÙ\Š
HOH	Ø\›Ý™Y	Î‚ˆˆHÛX[—Û˜[YJ‹™Ù]
	Û˜[YIÊJBˆYˆˆ[™‹›ÝÙ\Š
H›Ý[ˆ
	Ø[›Ûž[[Ý\ÉË	ÙÝY\Ý	Ë	Û˜IÊN‚ˆÛÝ[ÖÛ—H
ÏHBˆÜHÞÉÛ˜[YIÎˆ‹	Û‰ÎˆßH›Üˆ‹È[ˆÛÝ[Ë›[ÜÝØÛÛ[[ÛŠL
WBˆÓÓ‹Üš]WÝ^
œÛÛ‹™[\ÊÜ[œÝ\™WØ\ØÚZOQ˜[ÙK[™[LJK[˜ÛÙ[™ÏIÝ]‹N	ÊB‚ˆš[
‰Ø\YYÛ—Ø\YYH\›Ý™YY][YH™\ÜÈ	Âˆ‰ÊÝ[Ý™\œšYHÝÜ][Y\È›ÝÎˆÜÝ[J[ŠŠH›Üˆˆ[ˆÝ‹˜[Y\Ê
J_JIÊBˆYˆÚÚ\Y‚ˆš[
‰ÜÚÚ\YÛ[ŠÚÚ\Y
_H\›Ý™Y›ÝÜÈÚ]Z\ÜÚ[™È\ËÜÝÜÝ[YIÊBˆš[
‰ØÛÛšX]ÜœÎˆÛ[ŠÜ
_IÊB‚‚šYˆ×Û˜[YW×ÈOH	××ÛXZ[—×ÉÎ‚ˆXZ[Š
B