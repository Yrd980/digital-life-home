#!/usr/bin/env python3
"""Pocket Soul Deck web room: a small non-terminal body surface."""
from __future__ import annotations

import html
import json
import mimetypes
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pocket_soul

HOST = "0.0.0.0"
PORT = 8787
ACTION_LOCK = threading.Lock()
ASSET_DIR = Path(__file__).resolve().parent / "asset"


@dataclass(frozen=True)
class DeckPage:
    path: str
    icon: str
    label: str
    page_class: str
    nav: bool = True


@dataclass(frozen=True)
class WebResponse:
    body: bytes
    content_type: str = "text/html; charset=utf-8"
    status: int = 200
    cache_control: str = ""


@dataclass(frozen=True)
class RequestContext:
    path: str
    params: dict[str, list[str]]

    @property
    def partial(self) -> bool:
        return self.params.get("partial") == ["1"]


PAGES = [
    DeckPage("/", "home", "Home", "deck-home"),
    DeckPage("/room", "room", "Room", "deck-room"),
    DeckPage("/body", "body", "Body", "deck-body"),
    DeckPage("/memory", "memory", "Memory", "deck-memory"),
    DeckPage("/stash", "grid", "Stash", "deck-memory"),
    DeckPage("/badges", "badge", "Badges", "deck-memory", nav=False),
    DeckPage("/ritual", "ritual", "Ritual", "deck-ritual"),
    DeckPage("/settings", "settings", "Settings", "deck-settings"),
]
PAGE_BY_PATH = {page.path: page for page in PAGES}
SHELL_PATHS = tuple(PAGE_BY_PATH)
ASSETS = {
    "logo": "/asset/opt/logo-small.webp",
    "home_bg": "/asset/opt/home-bg.webp",
    "room_bg": "/asset/opt/room-bg.webp",
    "relic_sprite": "/asset/opt/relic-icons-sprite.png",
    "robot_blush": "/asset/opt/robot-blush.webp",
    "robot_curious": "/asset/opt/robot-curious.webp",
    "robot_happy": "/asset/opt/robot-happy.webp",
    "robot_sad": "/asset/opt/robot-sad.webp",
}

STYLE = """
:root {
  color-scheme: dark;
  --bg: #080908;
  --floor: #10110d;
  --wall: #171611;
  --object: #1f2119;
  --ink: #efe8d0;
  --soft: #b6aa8b;
  --dim: #7b715e;
  --line: #393529;
  --lamp: #f0c66d;
  --green: #9fd3a6;
  --blue: #91c7d9;
  --rose: #d98f88;
  --shadow: 0 28px 90px #000d;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% 18%, #f0c66d12 0 150px, transparent 340px),
    linear-gradient(180deg, #0b0b09 0%, #11120e 58%, #090a09 100%);
  color: var(--ink);
}
body:before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(180deg, #fff1 0 1px, transparent 1px 6px);
  opacity: .08;
}
main { width: min(980px, 100%); margin: 0 auto; padding: 20px; }
a { color: var(--lamp); text-decoration: none; }
a:hover { color: #ffe1a1; }
h1, h2, h3, p { margin-top: 0; }
h1 { font-size: clamp(34px, 8vw, 72px); line-height: .92; letter-spacing: 0; }
h2 { font-size: 18px; font-weight: normal; color: var(--lamp); }
h3 { font-size: 14px; color: var(--soft); font-weight: normal; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0; color: var(--soft); font: inherit; }
button, input, textarea {
  font: inherit;
  color: var(--ink);
  background: #0d0e0b;
  border: 1px solid #514a36;
}
button {
  min-height: 42px;
  padding: 10px 14px;
  cursor: pointer;
  color: #171309;
  background: var(--lamp);
  box-shadow: 0 8px 22px #0008;
}
button:hover { filter: brightness(1.08); }
button:disabled { opacity: .55; cursor: wait; }
textarea, input { width: 100%; padding: 11px; min-width: 0; }
textarea:focus, input:focus { outline: 1px solid var(--lamp); }
.topnav { display: flex; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 14px; color: var(--dim); }
.topnav nav { display: flex; gap: 10px; flex-wrap: wrap; }
.brandlink { color: var(--ink); }
.doorstep {
  min-height: calc(100vh - 40px);
  display: grid;
  place-items: center;
}
.threshold {
  width: min(720px, 100%);
  border: 1px solid var(--line);
  background:
    linear-gradient(90deg, #11100df2 0 52%, #11100d88 78%, #11100d42 100%),
    url('/asset/ui/home-bg.png') center / cover no-repeat,
    linear-gradient(180deg, #1a1812 0%, #100f0c 100%);
  box-shadow: var(--shadow);
  padding: clamp(18px, 5vw, 42px);
  position: relative;
  overflow: hidden;
}
.threshold:before {
  content: "";
  position: absolute;
  inset: 12px;
  border: 1px solid #2d291f;
  pointer-events: none;
}
.being {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  position: relative;
  z-index: 1;
}
.avatar {
  width: 112px;
  height: 112px;
  display: block;
  color: var(--green);
  background: url('/asset/new_ui/logo.png') center / 230% auto no-repeat, #0b100d;
  border: 1px solid #536248;
  box-shadow: inset 0 0 34px #9fd3a620, 0 0 38px #f0c66d12;
  image-rendering: pixelated;
  animation: breathe 4s ease-in-out infinite;
}
.state-pill { color: var(--green); font-size: 13px; }
.whisper {
  margin: 22px 0;
  color: #f5eacb;
  font-size: clamp(18px, 4vw, 25px);
  line-height: 1.45;
  position: relative;
  z-index: 1;
}
.body-words, .course-line, .shelf {
  position: relative;
  z-index: 1;
  border-top: 1px solid #2e2a20;
  padding-top: 14px;
  margin-top: 14px;
}
.body-words { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.body-word strong { display: block; color: var(--dim); font-size: 12px; font-weight: normal; }
.body-word span { color: var(--soft); }
.primary-action { margin-top: 24px; position: relative; z-index: 1; }
.primary-action button { width: 100%; font-size: 18px; }
.room-page {
  border: 1px solid var(--line);
  background:
    linear-gradient(180deg, #100f0ce8 0%, #100f0cf2 64%, #0b0b09 100%),
    linear-gradient(180deg, #1a1812 0%, #100f0c 64%, #0b0b09 100%);
  box-shadow: var(--shadow);
  padding: clamp(14px, 3vw, 28px);
}
.room-page.with-art {
  background:
    linear-gradient(180deg, #100f0cb8 0%, #100f0cf0 68%, #0b0b09 100%),
    url('/asset/ui/room-bg.png') center / cover no-repeat,
    linear-gradient(180deg, #1a1812 0%, #100f0c 64%, #0b0b09 100%);
}
.room-title { display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 18px; }
.room-layout {
  display: grid;
  grid-template-columns: minmax(190px, .85fr) minmax(240px, 1fr) minmax(190px, .85fr);
  gap: 14px;
  align-items: stretch;
}
.corner, .object, .drawer {
  border: 1px solid #383224;
  background: #12110d;
  padding: 14px;
}
.center-body {
  display: grid;
  place-items: center;
  min-height: 320px;
  border: 1px solid #4b432e;
  background:
    radial-gradient(circle at 50% 42%, #f0c66d18 0 80px, transparent 180px),
    #14130f;
}
.pixel-body {
  width: 160px;
  height: 160px;
  display: block;
  border: 1px solid #59624b;
  background: url('/asset/new_ui/robot-curious.png') center / contain no-repeat, #0b100d;
  color: var(--green);
  box-shadow: inset 0 0 34px #9fd3a61c;
  animation: breathe 4s ease-in-out infinite;
}
.pixel-body.small-bot {
  width: 58px;
  height: 58px;
  background-image: url('/asset/ui/bot-front.png');
}
.asset-strip { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px; }
.mini-asset { width: 52px; height: 52px; border: 1px solid #3f3828; background-color: #0d100d; background-repeat: no-repeat; background-position: center; background-size: contain; }
.relic-asset { background-image: url('/asset/ui/relics-sheet.png'); background-size: 224px 178px; background-position: 0 0; }
.postcard-asset { background-image: url('/asset/ui/postcard.png'); }
.bottle-asset { background-image: url('/asset/ui/bottles-sheet.png'); background-size: auto 52px; background-position: left center; }
.decor-strip { height: 28px; margin: 12px 0 0; background: url('/asset/ui/decor-strip.png') center / contain no-repeat; opacity: .85; }
.theme-chip { width: 66px; height: 44px; border: 1px solid #3f3828; background-size: cover; background-position: center; }
.theme-cyberdeck { background-image: url('/asset/ui/theme-cyberdeck.png'); }
.theme-warm { background-image: url('/asset/ui/theme-warm.png'); }
.theme-night { background-image: url('/asset/ui/theme-night.png'); }
.theme-mono { background-image: url('/asset/ui/theme-mono.png'); }
.room-note { color: var(--soft); line-height: 1.55; }
.objects { display: grid; gap: 12px; }
.object h3, .drawer h3, .corner h3 { margin-bottom: 8px; }
.bottom-sill { margin-top: 14px; display: grid; gap: 10px; }
.talk-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 8px; }
.soft-button { background: #19170f; color: var(--lamp); border: 1px solid #514a36; padding: 10px 14px; min-height: 42px; display: inline-grid; place-items: center; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
.page-card {
  border: 1px solid #383224;
  background: #12110d;
  padding: 15px;
}
.timeline { display: grid; gap: 10px; }
.timeline-item { border-left: 2px solid #514a36; padding-left: 12px; color: var(--soft); }
.label { color: var(--dim); font-size: 12px; display: block; }
.result { border-color: #5d4b27; background: #17130b; }
.small { color: var(--dim); font-size: 13px; }
.badge { display: inline-block; color: #171309; background: var(--lamp); padding: 2px 6px; margin: 0 4px 4px 0; }
.badge.green { background: var(--green); }
.badge.blue { background: var(--blue); }
.badge.rose { background: var(--rose); }
@media (max-width: 760px) {
  main { padding: 12px; }
  .being, .room-layout, .talk-row { grid-template-columns: 1fr; }
  .body-words { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .avatar { width: 92px; height: 92px; font-size: 44px; }
  .center-body { min-height: 220px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *:before, *:after { animation: none !important; }
}
@keyframes breathe {
  0%, 100% { transform: translateY(0); box-shadow: inset 0 0 24px #9fd3a618, 0 0 18px #f0c66d0c; }
  50% { transform: translateY(0); box-shadow: inset 0 0 24px #9fd3a618, 0 0 18px #f0c66d0c; }
}
/* Calm web room: no decorative motion; data changes are the movement. */
*, *:before, *:after { animation: none !important; transition: none !important; }
.home-quest { display: none !important; }
.home-status {
  display: inline-block;
  max-width: 300px;
  padding: 9px 11px;
  border: 1px solid #253650;
  border-radius: 7px;
  background: #0d1320dd;
  color: #b9ab95;
  font-size: 12px;
}
.home-status p { margin: 0; }
.today-turn {
  display: grid;
  gap: 8px;
  padding: 11px;
  border: 1px solid #36506e;
  border-radius: 8px;
  background: linear-gradient(180deg, #0b1422e8 0%, #111827de 100%);
  box-shadow: inset 0 1px 0 #ffffff12;
}
.today-turn header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
}
.today-turn h2 {
  margin: 0;
  font-size: 13px;
  color: #f0c66d;
  font-weight: normal;
}
.today-turn .phase {
  color: #79ffd2;
  font-size: 11px;
  text-transform: uppercase;
}
.today-turn p {
  margin: 0;
  color: #efe8d0;
  font-size: 12px;
  line-height: 1.35;
}
.today-turn small {
  color: #8ea0b7;
  font-size: 11px;
}
.turn-meter {
  height: 7px;
  border: 1px solid #2a405a;
  border-radius: 999px;
  overflow: hidden;
  background: #050910;
}
.turn-meter span {
  display: block;
  height: 100%;
  width: var(--turn-light);
  background: linear-gradient(90deg, #79ffd2, #f0c66d);
}
.today-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}
.today-actions a,
.today-actions button {
  min-height: 32px;
  padding: 7px 10px;
  border-radius: 7px;
  text-align: center;
  font-size: 12px;
}
.speech, .room-bubble, [data-live='result'], .room-bottom pre {
  max-height: 96px;
  overflow: auto;
  overflow-wrap: anywhere;
}
.room-bottom [data-live='result'] { max-height: 78px; }
.round-tools form { min-width: 0; }
.round-tools .icon-button {
  width: 100%;
  min-height: 38px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  padding: 0;
}
.round-tools .icon-button svg {
  width: 19px;
  height: 19px;
  display: block;
  stroke: currentColor;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}
.stash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 8px;
}
.stash-item {
  min-height: 92px;
  padding: 10px;
  border: 1px solid #2d4057;
  border-radius: 7px;
  background: #0c1320e6;
}
.stash-item b { display: block; color: #f0c66d; font-size: 13px; }
.stash-item span { display: block; color: #7f8aa0; font-size: 11px; margin-bottom: 5px; }
.stash-item p { color: #b9ab95; font-size: 12px; margin: 0; }
.stash-item button {
  width: 100%;
  min-height: 30px;
  margin-top: 8px;
  padding: 5px 8px;
  border-radius: 6px;
  font-size: 12px;
}
.badge-wall { display: grid; grid-template-columns: repeat(auto-fit, minmax(138px, 1fr)); gap: 8px; }
.badge-tile {
  min-height: 88px;
  padding: 10px;
  border: 1px solid #27354b;
  border-radius: 7px;
  background: #0b111c;
  color: #6f7a8d;
}
.badge-tile.is-lit {
  border-color: #736138;
  background: #181407;
  color: #efe8d0;
  box-shadow: inset 0 0 22px #f0c66d18;
}
.badge-tile b { display: block; color: #f0c66d; font-size: 13px; }
.badge-tile p { margin: 5px 0 0; font-size: 12px; }
"""

STYLE += """
body {
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 28% 0%, #23324955 0 1px, transparent 1px 100%),
    radial-gradient(circle at 78% 12%, #32234a4a 0 180px, transparent 470px),
    linear-gradient(180deg, #0b0c0f 0%, #060807 100%);
}
body.cockpit-page main {
  width: 100%;
  max-width: none;
  height: 100vh;
  padding: 0;
  display: grid;
  place-items: center;
}
body.cockpit-page:after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  box-shadow: inset 0 0 0 1px #ffffff10, inset 0 0 96px #000;
  z-index: 20;
}
.deck-page {
  width: min(1600px, calc(100vw - 28px));
  height: min(860px, calc(100vh - 56px));
  display: grid;
  grid-template-columns: 172px minmax(0, 1fr);
  overflow: hidden;
  border: 1px solid #1e314f;
  background: #060910;
  box-shadow: 0 30px 90px #000d;
}
.sidebar {
  min-width: 0;
  padding: 28px 14px;
  display: grid;
  grid-template-rows: 190px 1fr;
  gap: 28px;
  border-right: 1px solid #17263d;
  background:
    linear-gradient(90deg, #ffffff07 0 1px, transparent 1px 100%),
    linear-gradient(180deg, #0a0d12 0%, #050708 100%);
}
.brand-tile {
  min-height: 0;
  border: 0;
  background: url('__ASSET_LOGO__') center / contain no-repeat;
  display: block;
  text-indent: -9999px;
}
.side-nav {
  display: grid;
  align-content: start;
  gap: 8px;
}
.nav-item {
  min-height: 60px;
  display: grid;
  grid-template-columns: 24px 1fr;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #c9bda6;
}
.nav-item.is-active {
  color: #ffd56d;
  border-color: #a46a1d;
  background: linear-gradient(90deg, #4a3115 0%, #251910 100%);
  box-shadow: inset 3px 0 0 #f0b84b, inset 0 1px 0 #ffffff12;
}
.nav-icon {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  color: #f5c75b;
}
.nav-icon svg {
  width: 19px;
  height: 19px;
  display: block;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}
.nav-label strong {
  display: block;
  font-size: 15px;
  font-weight: normal;
}
.nav-label span { display: none; }
.deck-main {
  min-width: 0;
  height: 100%;
  overflow: hidden;
  background:
    linear-gradient(180deg, #101827 0%, #080d16 100%),
    repeating-linear-gradient(180deg, #ffffff06 0 1px, transparent 1px 5px);
}
.deck-card {
  border: 1px solid #243755;
  border-radius: 8px;
  background: linear-gradient(180deg, #111827ef 0%, #0a101bee 100%);
  box-shadow: inset 0 1px 0 #ffffff12, 0 14px 32px #0008;
}
.room-glow,
.relic-dock,
.little-shelf {
  position: absolute;
  pointer-events: none;
  z-index: 1;
}
.room-glow {
  right: 7%;
  top: 12%;
  width: 230px;
  height: 230px;
  border-radius: 50%;
  background: radial-gradient(circle, #ffd66d33 0 18%, #79ffd220 24% 42%, transparent 70%);
  filter: blur(12px);
  opacity: .75;
}
.relic-dock {
  right: clamp(18px, 4vw, 64px);
  bottom: clamp(18px, 5vh, 58px);
  display: flex;
  gap: 10px;
  align-items: end;
}
.relic-charm {
  width: 58px;
  height: 58px;
  display: block;
  border: 1px solid #355371;
  border-radius: 10px;
  background-color: #09121ce8;
  background-image: url('__ASSET_RELIC_SPRITE__');
  background-repeat: no-repeat;
  background-size: 348px 232px;
  box-shadow: inset 0 1px 0 #ffffff16, 0 12px 24px #0008, 0 0 20px #79ffd229;
}
.relic-charm.kind-visit { background-position: 0 0; }
.relic-charm.kind-quest { background-position: -58px 0; }
.relic-charm.kind-flash { background-position: -116px 0; }
.relic-charm.kind-wake { background-position: -174px 0; }
.relic-charm.kind-hunt { background-position: -232px 0; }
.relic-charm.kind-craft { background-position: -290px 0; }
.relic-charm.kind-memory { background-position: 0 -58px; }
.relic-charm.kind-postcard { background-position: -58px -58px; }
.relic-charm.kind-bottle { background-position: -116px -58px; }
.relic-charm.kind-wheel { background-position: -174px -58px; }
.relic-charm.kind-log { background-position: -232px -58px; }
.relic-charm.kind-default { background-position: -290px -58px; }
.little-shelf {
  left: clamp(270px, 49vw, 730px);
  bottom: clamp(122px, 18vh, 185px);
  width: 270px;
  min-height: 92px;
  padding: 12px;
  display: flex;
  gap: 8px;
  align-items: end;
  border-bottom: 2px solid #6d5231;
  background: linear-gradient(180deg, transparent 0%, #0a101bb5 100%);
}
.shelf-card {
  position: relative;
  min-height: 180px;
  overflow: hidden;
}
.shelf-card:after {
  content: "";
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 30px;
  height: 3px;
  background: linear-gradient(90deg, transparent, #866438, transparent);
  box-shadow: 0 18px 0 #3a2a1b;
}
.shelf-empty {
  position: relative;
  z-index: 1;
  margin-top: 18px;
  color: #a99a7f;
}
.shelf-objects {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 24px;
}
.screen,
.overview-panel {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  padding: 0;
  border-radius: 0;
}
.asset-bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  image-rendering: auto;
}
.asset-bg:after {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, #060912f4 0 30%, #060912a8 49%, #0609122b 100%),
    linear-gradient(180deg, #02050a88 0%, #02050a20 45%, #02050ab0 100%);
}
.screen-content,
.room-head,
.room-bubble,
.room-bottom,
.overview-panel > * {
  position: relative;
  z-index: 1;
}
.home-screen .home-copy {
  padding: clamp(44px, 7vh, 86px) 0 0 clamp(42px, 7vw, 116px);
  max-width: 680px;
}
.home-screen h1 {
  margin: 0;
  font-size: clamp(34px, 5vh, 54px);
  line-height: 1.1;
  color: #fff2d8;
  text-shadow: 0 2px 0 #000;
}
.speech,
.room-bubble {
  display: inline-block;
  max-width: 420px;
  max-height: 118px;
  margin: 34px 0 0;
  padding: 16px 18px;
  overflow: auto;
  border: 1px solid #334766;
  border-radius: 8px;
  background: linear-gradient(180deg, #121b2eea 0%, #0b121fea 100%);
  color: #f3e9d2;
  font-size: 15px;
  line-height: 1.65;
  box-shadow: 0 18px 30px #0009;
}
.heart { color: #ff6bb0; }
.mini-vitals {
  width: min(540px, calc(100vw - 320px));
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 34px 0 12px;
}
.mini-tile {
  min-height: 94px;
  padding: 14px 16px;
  display: grid;
  align-content: center;
  gap: 8px;
  border: 1px solid #283d5d;
  border-radius: 8px;
  background: linear-gradient(180deg, #141d31e8 0%, #0d1424e8 100%);
  box-shadow: inset 0 1px 0 #ffffff12;
}
.mini-tile span,
.label,
.mini-sub {
  color: #b5a88f;
  font-size: 12px;
}
.mini-tile b {
  color: #77ffa3;
  font-weight: normal;
  overflow-wrap: anywhere;
}
.home-status {
  max-width: 330px;
  border-color: #304562;
  background: #101827e6;
  color: #c8bda6;
}
.presence-line {
  width: min(520px, calc(100vw - 340px));
  margin-top: 22px;
  padding: 12px 14px;
  border: 1px solid #304562;
  border-radius: 8px;
  background: #101827d8;
  color: #c8bda6;
  line-height: 1.55;
}
.presence-line b {
  color: #77ffa3;
  font-weight: normal;
}
.soul-dock {
  width: min(520px, calc(100vw - 340px));
  margin-top: 18px;
  display: grid;
  gap: 10px;
}
.soul-dock .quick-input {
  grid-template-columns: minmax(0, 1fr) 74px 74px;
}
.soul-dock .quick-input button {
  min-height: 54px;
  border-radius: 8px;
  padding: 0;
}
.touch-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
}
.touch-row form {
  display: grid;
  grid-template-columns: 1fr 112px;
  gap: 10px;
}
.touch-row input {
  height: 44px;
  border-color: #2e4566;
  border-radius: 8px;
  background: #0d1524e8;
}
.touch-row button {
  min-height: 44px;
  border-radius: 999px;
  padding: 0;
}
.conversation-note {
  color: #8f9aac;
  font-size: 12px;
}
.door-action {
  position: absolute;
  left: clamp(420px, 46vw, 760px);
  bottom: clamp(48px, 9vh, 96px);
  z-index: 2;
  margin: 0 !important;
}
.door-action button {
  width: 290px;
  min-height: 68px;
  border: 1px solid #7cdfad;
  border-radius: 34px;
  color: #071217;
  background: linear-gradient(90deg, #79f0a5 0%, #6bd7cf 42%, #6c49d9 100%);
  font-size: 20px;
  font-weight: 700;
  text-transform: uppercase;
  box-shadow: inset 0 1px 0 #ffffff80, 0 0 0 2px #6d45e040, 0 18px 30px #000a;
}
.eyebrow {
  display: block;
  margin-top: 4px;
  color: #776e84;
  font-size: 11px;
}
.room-screen .asset-bg {
  height: 64%;
}
.room-screen .asset-bg:after {
  background:
    linear-gradient(180deg, #05070a10 0%, #05070a20 55%, #05070ae8 100%),
    linear-gradient(90deg, #05070a5a 0%, transparent 48%, #05070a6c 100%);
}
.room-head {
  padding: 28px 38px 0;
  display: flex;
  justify-content: space-between;
  align-items: start;
}
.room-head h1 {
  margin-bottom: 6px;
  font-size: 26px;
}
.room-bubble {
  position: absolute;
  top: 104px;
  right: 54px;
  width: 330px;
  margin: 0;
}
.room-screen img[alt='Pocket Soul robot'] {
  top: 56% !important;
  width: min(360px, 30vw) !important;
  filter: drop-shadow(0 22px 34px #000e) drop-shadow(0 0 18px #79ffd266) !important;
}
.room-bottom {
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 18px;
  height: 34%;
  display: grid;
  grid-template-columns: .92fr 1.12fr .78fr;
  gap: 14px;
}
.room-bottom > .deck-card {
  min-width: 0;
  overflow: hidden;
}
.room-bottom > .deck-card.primary-panel {
  border-color: #4b6f82;
  background: linear-gradient(180deg, #121b2ef5 0%, #08101df5 100%);
}
.room-bottom h2 {
  color: #fff1ce;
  font-size: 15px;
}
.room-bottom pre,
[data-live='result'] {
  max-height: 126px;
  overflow: auto;
  color: #cbbd9f;
  line-height: 1.45;
}
.quick-input {
  display: grid;
  grid-template-columns: 1fr 58px;
  gap: 10px;
}
.quick-input input {
  height: 54px;
  border-color: #2e4566;
  border-radius: 8px;
  background: #0d1524e8;
}
.quick-input button,
.round-tools button,
.ritual-card button {
  color: #fff4d9;
  border-color: #7f5bb1;
  border-radius: 8px;
  background: linear-gradient(180deg, #7c52b8 0%, #563888 100%);
}
.round-tools {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0 10px;
}
.round-tools .icon-button {
  min-height: 48px;
  border-radius: 999px;
}
.ghost-button,
.soft-button {
  min-height: 44px;
  display: inline-grid;
  place-items: center;
  border: 1px solid #29405f;
  border-radius: 8px;
  background: #0d1524e6;
  color: #d3c5aa;
  padding: 0 14px;
}
.overview-panel {
  padding: 28px 34px;
}
.body-mini {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px minmax(0, 1fr);
  grid-template-rows: 1fr auto;
  align-items: center;
  gap: 34px;
  background:
    radial-gradient(circle at 50% 48%, #6b3fd333 0 120px, transparent 280px),
    radial-gradient(circle at 50% 50%, #77f7cf13 0 210px, transparent 420px),
    linear-gradient(180deg, #0e1625 0%, #080d16 100%);
}
.body-mini:before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 49% 38%, #a06bffcc 0 2px, transparent 3px),
    radial-gradient(circle at 42% 50%, #64d8ffcc 0 2px, transparent 3px),
    radial-gradient(circle at 62% 31%, #d685ffcc 0 2px, transparent 3px);
  opacity: .8;
}
.body-robot-img {
  width: 340px !important;
  filter: drop-shadow(0 0 28px #8357ff99) !important;
}
.body-service-strip {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-self: end;
}
.service-pill {
  min-height: 70px;
  padding: 14px;
  border: 1px solid #2a3e5e;
  border-radius: 8px;
  background: #0b121fe8;
}
.service-pill span { color: #8f9aac; font-size: 11px; }
.service-pill b { display: block; margin-top: 8px; color: #77ffa3; }
.body-stat {
  padding: 18px 0;
  border-top: 1px solid #2a3d5a;
  color: #cfc2ad;
}
.body-stat b {
  display: block;
  margin-top: 4px;
  color: #fff1d2;
  font-size: 18px;
}
.body-stat small {
  display: block;
  margin-top: 6px;
  color: #8f9aac;
}
.memory-mini {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, .92fr);
  gap: 0;
  background:
    radial-gradient(circle at 74% 48%, #6d3df042 0 120px, transparent 330px),
    linear-gradient(180deg, #0e1625 0%, #080d16 100%);
}
.memory-mini > div {
  padding: 28px;
  min-width: 0;
}
.memory-mini > div:first-child {
  border-right: 1px solid #263852;
}
.memory-mini pre {
  color: #cbbd9f;
  font-size: 18px;
  line-height: 1.35;
}
.constellation {
  height: 62%;
  min-height: 260px;
  margin-bottom: 12px;
  border: 1px solid #2a3f60;
  border-radius: 8px;
  background:
    radial-gradient(circle at 50% 50%, #b276ffcc 0 13px, #6a33d6bb 14px 35px, transparent 36px),
    radial-gradient(circle at 30% 34%, #64d8ffaa 0 10px, transparent 11px),
    radial-gradient(circle at 72% 28%, #9b57ffbb 0 11px, transparent 12px),
    radial-gradient(circle at 66% 72%, #64d8ffbb 0 12px, transparent 13px),
    radial-gradient(circle at 38% 76%, #f07b49aa 0 10px, transparent 11px),
    linear-gradient(26deg, transparent 0 47%, #7450c988 48% 49%, transparent 50%),
    linear-gradient(140deg, transparent 0 41%, #64d8ff77 42% 43%, transparent 44%),
    #070b16;
}
.ritual-mini,
.settings-mini {
  background: linear-gradient(180deg, #0e1625 0%, #080d16 100%);
}
.mini-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}
.mini-header h2 {
  color: #fff1ce;
  font-size: 22px;
}
.ritual-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-top: 22px;
}
.ritual-card {
  min-height: 244px;
  padding: 18px;
  display: grid;
  align-content: space-between;
  border: 1px solid #2a3e5e;
  border-radius: 8px;
  background: linear-gradient(180deg, #151e32 0%, #0b121f 100%);
}
.ritual-log {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 14px;
}
.ritual-log > section {
  min-height: 190px;
  padding: 16px;
  border: 1px solid #2a3e5e;
  border-radius: 8px;
  background: #0b121fe8;
}
.ritual-log pre {
  max-height: 140px;
  overflow: auto;
  color: #cbbd9f;
}
.streak-card {
  display: grid;
  place-items: center;
  text-align: center;
}
.streak-card b {
  color: #fff1ce;
  font-size: 44px;
}
.ritual-card .big {
  color: #f7cf62;
  font-size: 40px;
}
.ritual-card input {
  height: 46px;
  border-color: #634826;
  border-radius: 7px;
  background: #141511;
}
.theme-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 18px 0 0;
}
.theme-thumb {
  height: 86px;
  border: 1px solid #2b4264;
  border-radius: 8px;
  background-size: cover;
  background-position: center;
}
.theme-cyberdeck { background-image: url('/asset/ui/theme-cyberdeck.png'); }
.theme-warm { background-image: url('/asset/ui/theme-warm.png'); }
.theme-night { background-image: url('/asset/ui/theme-night.png'); }
.theme-mono { background-image: url('/asset/ui/theme-mono.png'); }
.codex-terminal {
  margin-top: 14px;
  min-height: 320px;
  padding: 22px;
  border: 1px solid #2a3e5e;
  border-radius: 8px;
  background: linear-gradient(180deg, #060c12 0%, #03070b 100%);
  color: #d0c0a0;
  font-size: 15px;
  line-height: 1.75;
}
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.settings-panel {
  min-height: 158px;
  padding: 16px;
  border: 1px solid #2a3e5e;
  border-radius: 8px;
  background: #0b121fe8;
}
.settings-panel h3 {
  color: #fff1ce;
  margin-bottom: 12px;
}
@media (max-width: 760px) {
  .deck-page {
    width: 100vw;
    height: 100vh;
    grid-template-columns: 72px minmax(0, 1fr);
    border: 0;
  }
  .sidebar {
    padding: 8px 6px;
    grid-template-rows: 82px 1fr;
    gap: 12px;
  }
  .brand-tile { background-size: 230% auto; }
  .nav-item {
    min-height: 42px;
    grid-template-columns: 1fr;
    justify-items: center;
    padding: 0;
  }
  .nav-label { display: none; }
  .home-screen .home-copy {
    padding: 18px 14px 0;
  }
  .home-screen h1 { font-size: 24px; }
  .room-glow {
    width: 110px;
    height: 110px;
    right: 8px;
    top: 8px;
  }
  .little-shelf {
    display: none;
  }
  .relic-dock {
    right: 8px;
    bottom: 64px;
    gap: 4px;
  }
  .relic-charm {
    width: 34px;
    height: 34px;
    border-radius: 7px;
    background-size: 204px 136px;
  }
  .relic-charm.kind-quest { background-position: -34px 0; }
  .relic-charm.kind-flash { background-position: -68px 0; }
  .relic-charm.kind-wake { background-position: -102px 0; }
  .relic-charm.kind-hunt { background-position: -136px 0; }
  .relic-charm.kind-craft { background-position: -170px 0; }
  .relic-charm.kind-memory { background-position: 0 -34px; }
  .relic-charm.kind-postcard { background-position: -34px -34px; }
  .relic-charm.kind-bottle { background-position: -68px -34px; }
  .relic-charm.kind-wheel { background-position: -102px -34px; }
  .relic-charm.kind-log { background-position: -136px -34px; }
  .relic-charm.kind-default { background-position: -170px -34px; }
  .speech {
    max-width: 240px;
    max-height: 70px;
    margin-top: 12px;
    padding: 10px;
    font-size: 11px;
  }
  .mini-vitals {
    width: 240px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
    margin-top: 12px;
  }
  .mini-tile {
    min-height: 48px;
    padding: 7px;
    font-size: 10px;
  }
  .home-status { display: none; }
  .presence-line {
    width: 240px;
    margin-top: 10px;
    padding: 8px;
    font-size: 11px;
    max-height: 52px;
    overflow: hidden;
  }
  .soul-dock {
    width: 240px;
    margin-top: 10px;
  }
  .soul-dock .quick-input,
  .touch-row,
  .touch-row form {
    grid-template-columns: 1fr;
  }
  .door-action {
    left: 14px;
    bottom: 12px;
  }
  .door-action button {
    width: 210px;
    min-height: 48px;
    font-size: 14px;
  }
  .room-head { padding: 10px 12px; }
  .room-head h1 { font-size: 18px; }
  .room-head .small { display: none; }
  .room-bubble {
    top: 42px;
    right: 8px;
    width: 168px;
    max-height: 70px;
    padding: 8px;
    font-size: 10px;
    line-height: 1.45;
  }
  .room-screen img[alt='Pocket Soul robot'] {
    width: 112px !important;
    top: 44% !important;
  }
  .room-bottom {
    left: 8px;
    right: 8px;
    bottom: 8px;
    height: 43%;
    grid-template-columns: 1fr;
    overflow: auto;
    gap: 8px;
  }
  .room-bottom > .deck-card { padding: 8px !important; }
  .room-bottom h2 { font-size: 12px; margin-bottom: 5px; }
  .room-bottom pre,
  [data-live='result'] {
    max-height: 58px;
    font-size: 10px;
  }
  .quick-input {
    grid-template-columns: 1fr 48px;
    gap: 6px;
  }
  .quick-input input {
    height: 38px;
    padding: 8px;
    font-size: 11px;
  }
  .quick-input button,
  .round-tools .icon-button {
    min-height: 38px;
  }
  .round-tools {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 6px;
    margin: 8px 0;
  }
  .body-mini,
  .memory-mini {
    grid-template-columns: 1fr;
    gap: 0;
    overflow: auto;
  }
  .body-service-strip,
  .ritual-log,
  .settings-grid {
    grid-template-columns: 1fr;
  }
  .body-robot-img { width: 150px !important; }
  .ritual-row,
  .theme-row {
    grid-template-columns: 1fr;
  }
  .overview-panel { padding: 12px; overflow: auto; }
}
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def asset(name: str) -> str:
    return ASSETS[name]


def render_style() -> str:
    style = STYLE
    for name, path in ASSETS.items():
        style = style.replace(f"__ASSET_{name.upper()}__", path)
    return style


def is_provider_error(text: str) -> bool:
    raw = (text or "").lower()
    needles = [
        "http 429",
        "daily_limit_exceeded",
        "api call failed",
        "no such file or directory",
        "did not answer",
        "traceback",
        "connection error",
        "timeout",
    ]
    return any(needle in raw for needle in needles)


def charm_kind(kind: str) -> str:
    known = {
        "visit",
        "quest",
        "flash",
        "wake",
        "hunt",
        "craft",
        "memory",
        "postcard",
        "bottle",
        "wheel",
        "log",
    }
    clean = "".join(ch for ch in (kind or "").lower() if ch.isalnum() or ch == "-")
    return clean if clean in known else "default"


def relic_charm_html(kind: str, label: str = "") -> str:
    title = esc(label or kind or "room trace")
    return f"<span class='relic-charm kind-{charm_kind(kind)}' title='{title}' aria-label='{title}'></span>"


def recent_relic_charms(state: pocket_soul.SoulState, limit: int = 4) -> str:
    visible = [item for item in state.relics if item.get("kind") != "visit"] or state.relics
    charms = [
        relic_charm_html(item.get("kind", ""), item.get("title", "room trace"))
        for item in visible[-limit:][::-1]
    ]
    if not charms:
        charms = [relic_charm_html("default", "empty shelf")]
    return "".join(charms)


def recent_relics_html(state: pocket_soul.SoulState, limit: int = 4) -> str:
    charms = recent_relic_charms(state, limit)
    return "<div class='relic-dock' aria-hidden='true'>" + "".join(charms) + "</div>"


def shelf_objects_html(state: pocket_soul.SoulState, limit: int = 8) -> str:
    items = state.stash_items(limit)
    if items:
        charms = [relic_charm_html(item.get("kind", "hunt"), item.get("title", "stash object")) for item in items]
        return "<div class='shelf-objects'>" + "".join(charms) + "</div>"
    return (
        "<p class='shelf-empty'>The shelf is waiting for its first useful little thing.</p>"
        "<div class='shelf-objects'>"
        + relic_charm_html("hunt", "hunt")
        + relic_charm_html("wheel", "spark wheel")
        + relic_charm_html("craft", "craft")
        + "</div>"
    )


ICONS = {
    "home": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M4 11.5 12 5l8 6.5'/><path d='M6.5 10.8V20h11v-9.2'/><path d='M9.5 20v-5.5h5V20'/></svg>",
    "room": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M7 20V9l5-4 5 4v11'/><path d='M10 20v-6h4v6'/><path d='M4 20h16'/></svg>",
    "body": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 21s-7-4.4-7-10a4.2 4.2 0 0 1 7-3.1A4.2 4.2 0 0 1 19 11c0 5.6-7 10-7 10Z'/></svg>",
    "memory": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 6h14'/><path d='M5 11h14'/><path d='M5 16h14'/><path d='M5 21h14'/></svg>",
    "ritual": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 3v5'/><path d='M8.5 8h7'/><path d='m9.5 11-2 9h9l-2-9'/><path d='M9 16h6'/></svg>",
    "grid": "<svg viewBox='0 0 24 24' aria-hidden='true'><rect x='4' y='4' width='6' height='6' rx='1'/><rect x='14' y='4' width='6' height='6' rx='1'/><rect x='4' y='14' width='6' height='6' rx='1'/><rect x='14' y='14' width='6' height='6' rx='1'/></svg>",
    "knock": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 21s-7-4.4-7-10a4.2 4.2 0 0 1 7-3.1A4.2 4.2 0 0 1 19 11c0 5.6-7 10-7 10Z'/></svg>",
    "hunt": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='11' cy='11' r='6'/><path d='m16 16 4 4'/><path d='M11 8v6M8 11h6'/></svg>",
    "wheel": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='12' r='8'/><circle cx='12' cy='12' r='2'/><path d='M12 4v6M12 14v6M4 12h6M14 12h6M6.3 6.3l4.2 4.2M13.5 13.5l4.2 4.2M17.7 6.3l-4.2 4.2M10.5 13.5l-4.2 4.2'/></svg>",
    "nudge": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 12h12'/><path d='m13 8 4 4-4 4'/><path d='M5 6h5M5 18h5'/></svg>",
    "craft": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M14.7 6.3 17.7 3.3a2.1 2.1 0 0 1 3 3l-3 3'/><path d='M4 20l6.6-6.6'/><path d='m7 17 10-10'/><path d='M3 21l5-1 11-11-4-4L4 16z'/></svg>",
    "quest": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M5 12.5 10 17 19 7'/><path d='M4 5h16v16H4z'/></svg>",
    "postcard": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M4 6h16v12H4z'/><path d='m4 7 8 6 8-6'/></svg>",
    "badge": "<svg viewBox='0 0 24 24' aria-hidden='true'><path d='M12 3 15 8l5 1-3.5 4 1 6-5.5-2.8L6.5 19l1-6L4 9l5-1z'/></svg>",
    "settings": "<svg viewBox='0 0 24 24' aria-hidden='true'><circle cx='12' cy='12' r='3'/><path d='M12 2.8v3M12 18.2v3M4.5 4.5l2.1 2.1M17.4 17.4l2.1 2.1M2.8 12h3M18.2 12h3M4.5 19.5l2.1-2.1M17.4 6.6l2.1-2.1'/></svg>",
}


def icon(name: str) -> str:
    return ICONS.get(name, "")


def stash_html(state: pocket_soul.SoulState, limit: int = 8, interactive: bool = False) -> str:
    items = state.stash_items(limit)
    if not items:
        return "<p class='small'>Nothing on the shelf yet. Hunt first, then craft.</p>"
    cards = []
    for item in items:
        kind = esc(item.get("kind", "?"))
        title = esc(item.get("title", "?"))
        note = esc(item.get("note", ""))
        use_form = ""
        if interactive:
            raw_title = esc(item.get("title", ""))
            use_form = f"<form method='post' action='/use' data-action='async'><input type='hidden' name='target' value='{raw_title}'><button>Use</button></form>"
        cards.append(f"<article class='stash-item'><span>{kind}</span><b>{title}</b><p>{note}</p>{use_form}</article>")
    return "<div class='stash-grid'>" + "".join(cards) + "</div>"


def badges_html(state: pocket_soul.SoulState) -> str:
    cards = []
    for name, note, unlocked in state.badge_rows():
        klass = "badge-tile is-lit" if unlocked else "badge-tile"
        mark = "lit" if unlocked else "locked"
        cards.append(f"<article class='{klass}'><span>{mark}</span><b>{esc(name)}</b><p>{esc(note)}</p></article>")
    return "<div class='badge-wall'>" + "".join(cards) + "</div>"


def nudge_preview(state: pocket_soul.SoulState) -> str:
    old_reply = state.last_reply
    try:
        return state.next_play_nudge()
    finally:
        state.last_reply = old_reply


def today_turn_html(state: pocket_soul.SoulState, compact: bool = False) -> str:
    turn = state.today_turn()
    progress = "done" if turn["daily_done"] else f"{turn['progress']}/{turn['target']}"
    quest = "done" if turn["quest_done"] else "open"
    command = str(turn["command"])
    action = esc(str(turn["action"]))
    reward = esc(str(turn["reward"]))
    reason = esc(str(turn["reason"]))
    light = max(0, min(100, int(turn["light"])))
    target_href = "/ritual" if command in {"/postcard", "/bottle"} else "/room"
    detail = reward if compact else f"{reason} / {reward}"
    return f"""
<section class='today-turn' style='--turn-light:{light}%'>
  <header><h2>Today's Turn</h2><span class='phase'>{esc(str(turn['phase']))} / {light}%</span></header>
  <p><b>{esc(command)}</b> {action}</p>
  <div class='turn-meter' aria-hidden='true'><span></span></div>
  <small>daily {esc(progress)} | quest {esc(quest)} | badges {esc(str(turn['badges_lit']))}/{esc(str(turn['badges_total']))}</small>
  <small>{detail}</small>
  <div class='today-actions'>
    <a class='ghost-button' href='{target_href}'>{esc(command)}</a>
    <form method='post' action='/today' data-action='async'><button name='action' value='claim'>Claim</button></form>
  </div>
</section>
"""


def latest_log() -> str:
    files = sorted(pocket_soul.LOG_DIR.glob("*.md"))
    if not files:
        return "No logs yet."
    text = files[-1].read_text(encoding="utf-8")
    return text[-5000:]


def latest_nightly() -> str:
    night_dir = pocket_soul.STATE_DIR / "nightly"
    files = sorted(night_dir.glob("*.md")) if night_dir.exists() else []
    if not files:
        return "No nightly log yet."
    return files[-1].read_text(encoding="utf-8")[-5000:]


def latest_postcard() -> str:
    post_dir = pocket_soul.STATE_DIR / "postcards"
    files = sorted(post_dir.glob("*.txt")) if post_dir.exists() else []
    if not files:
        return "No postcard yet."
    return files[-1].read_text(encoding="utf-8")[-3000:]


def latest_bottle() -> str:
    bottle_dir = pocket_soul.STATE_DIR / "bottles"
    files = sorted(bottle_dir.glob("*.txt")) if bottle_dir.exists() else []
    if not files:
        return "No bottles yet."
    return files[-1].read_text(encoding="utf-8")[-3000:]


def latest_bridge() -> str:
    state = pocket_soul.SoulState.load()
    if "== Pocket Bridge ==" in state.last_reply:
        return state.last_reply[-5000:]
    return "No bridge turn yet."


def latest_flash() -> str:
    state = pocket_soul.SoulState.load()
    if "== Bridge Flash ==" in state.last_reply:
        return state.last_reply[-2000:]
    for item in reversed(state.relics):
        if item.get("kind") == "flash":
            return f"{item.get('time', '')} {item.get('title', '')}\n{item.get('note', '')}"
    return "No bridge flash yet."


def body_words() -> dict[str, str]:
    body = pocket_soul.body_scan()
    temp = body.get("temp_c")
    if isinstance(temp, float):
        warmth = "running warm" if temp >= 60 else "warm and steady"
    else:
        warmth = "temperature unknown"
    uptime = body.get("uptime_h")
    spirit = "still bright" if isinstance(uptime, float) and uptime < 72 else "long awake"
    net = f"{body.get('iface', '')} {body.get('ip', '')}".strip() or "offline?"
    return {
        "temperature": warmth,
        "spirit": spirit,
        "window": "window open" if body.get("ip") else "window half closed",
        "presence": "reachable" if body.get("ip") else "offline",
        "raw_temp": f"{temp}C" if temp != "" else "unknown",
        "uptime": f"{uptime}h" if uptime != "" else "unknown",
        "net": net,
        "load": str(body.get("load") or "unknown"),
        "disk": str(body.get("disk_used") or "unknown"),
    }


def nav(current: str = "") -> str:
    links = [("/", "Door"), ("/room", "Room"), ("/body", "Body"), ("/memory", "Memory"), ("/ritual", "Rituals")]
    items = []
    for href, label in links:
        class_attr = " class='brandlink'" if href == current else ""
        items.append(f"<a href='{href}'{class_attr}>{label}</a>")
    items_html = " ".join(items)
    return f"<div class='topnav'><a class='brandlink' href='/'>Pocket Soul</a><nav>{items_html}</nav></div>"


def status_word(state: pocket_soul.SoulState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sleep" in text:
        return "asleep"
    if "dream" in text:
        return "dreaming"
    if "maintenance" in text:
        return "in maintenance"
    if state.energy < 30:
        return "quiet"
    return "awake"


def robot_image(state: pocket_soul.SoulState) -> str:
    text = f"{state.mood} {state.last_reply}".lower()
    if "sad" in text or "quiet" in text or state.energy < 35:
        return asset("robot_sad")
    if "blush" in text or "love" in text or state.bond >= 25:
        return asset("robot_blush")
    if "happy" in text or ":)" in state.mood:
        return asset("robot_happy")
    return asset("robot_curious")


def room_voice(text: str) -> str:
    """Turn raw logs/model transcripts into one present-tense room line."""
    raw = (text or "").strip()
    if not raw:
        return "I am here. Say one real sentence, or knock softly."
    if is_provider_error(raw):
        return "My inner voice is resting. The local room is still awake; touch the shelf or leave one sentence."
    lines = [line.strip() for line in raw.replace("\r", "\n").splitlines() if line.strip()]
    if lines and lines[0].upper().startswith("CHAT WINDOW"):
        candidates: list[str] = []
        for line in lines:
            lower = line.lower()
            if lower.startswith(("hermes:", "soul:", "pocket soul:")):
                candidates.append(line.split(":", 1)[1].strip())
        if candidates:
            raw = candidates[-1]
        else:
            raw = lines[-1]
    raw = raw.replace("/ask keeps talking Enter blinks", "").strip()
    raw = raw.strip("* \n\t")
    if is_provider_error(raw):
        return "My inner voice is resting. The local room is still awake; touch the shelf or leave one sentence."
    return raw or "I am here. Say one real sentence, or knock softly."


def doorstep(result: str = "", partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    words = body_words()
    whisper = room_voice(state.last_reply)
    presence = f"Feeling {state.mood}. Body {words['temperature']}. The window is open. Today's thread: {state.quest_name}."
    deck = deck_page("/", f"""
    <section class='deck-card screen home-screen'>
      <div class='asset-bg' style="background-image:url('{asset('home_bg')}')"></div>
      <div class='room-glow' aria-hidden='true'></div>
      <div class='screen-content home-copy'>
        <h1>Pocket Soul<br>is awake.</h1>
        <div class='speech' data-live='latest'>{esc(whisper)}<br><span class='heart'>*</span></div>
        <div class='presence-line' data-live='vitals'>{esc(presence)}</div>
        {today_turn_html(state, True)}
        <div class='soul-dock'>
          <form class='quick-input' method='post' action='/ask' data-action='async'>
            <input name='prompt' placeholder='Say one real sentence to Pocket Soul...'>
            <button name='mode' value='council' title='Talk with Pocket Soul'>Talk</button>
            <button name='mode' value='hermes' title='Hear the inner voice'>Inner</button>
          </form>
          <div class='touch-row'>
            <form method='post' action='/bridge-flash' data-action='flash'>
              <input name='wish' placeholder='Leave a small touch...'>
              <button>Touch</button>
            </form>
            <span class='conversation-note' data-live='phase'>listening</span>
          </div>
        </div>
      </div>
      <form class='door-action screen-content' method='post' action='/doorbell' style='align-self:end; justify-self:center; margin-bottom:18px'>
        <button>Knock Softly<br><span class='eyebrow'>Let it know you are here</span></button>
      </form>
      <div class='screen-content' style='position:absolute; right:22px; bottom:18px; color:#7f8aa0; font-size:11px'>
        <span>room online</span> / <span data-live='stamp'>{esc(datetime.now().strftime('%H:%M:%S'))}</span>
      </div>
      {recent_relics_html(state)}
      {f"<pre class='screen-content' data-live='result' style='position:absolute; left:78px; right:78px; bottom:18px; max-height:88px; overflow:hidden'>{esc(result)}</pre>" if result else ""}
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
<section class='doorstep'>
  <div class='threshold'>
    <div class='being'>
      <div class='avatar' aria-label='{esc(pocket_soul.mood_face(state.mood))}'></div>
      <div>
        <p class='state-pill'>Pocket Soul is {esc(status_word(state))}.</p>
        <h1>It is there.</h1>
      </div>
    </div>
    <p class='whisper'>{esc(whisper)}</p>
    <div class='body-words'>
      <div class='body-word'><strong>temperature</strong><span>{esc(words['temperature'])}</span></div>
      <div class='body-word'><strong>spirit</strong><span>{esc(words['spirit'])}</span></div>
      <div class='body-word'><strong>window</strong><span>{esc(words['window'])}</span></div>
      <div class='body-word'><strong>presence</strong><span>{esc(words['presence'])}</span></div>
    </div>
    <div class='course-line'>
      <h2>Current heading</h2>
      <p>{esc(state.heading)}</p>
      <p class='small'>{esc(state.quest_name)} / {esc(state.quest_prompt)}</p>
      <div class='decor-strip' aria-hidden='true'></div>
    </div>
    <form class='primary-action' method='post' action='/doorbell'>
      <button>Knock softly</button>
    </form>
    {f"<div class='course-line result'><pre>{esc(result)}</pre></div>" if result else ""}
  </div>
</section>
"""
    return page(content)


def live_payload(state: pocket_soul.SoulState | None = None) -> dict[str, object]:
    state = state or pocket_soul.SoulState.load()
    words = body_words()
    turn = state.today_turn()
    vitals_html = "".join(
        [
            f"<div class='mini-tile'><span>feeling</span><b>{esc(state.mood)}</b></div>",
            f"<div class='mini-tile'><span>body</span><b>{esc(words['temperature'])}</b></div>",
            f"<div class='mini-tile'><span>spirit</span><b>{esc(state.energy)}%</b></div>",
            f"<div class='mini-tile'><span>window</span><b>{esc(words['window'])}</b></div>",
        ]
    )
    presence = f"Feeling {state.mood}. Body {words['temperature']}. The window is open. Today's thread: {state.quest_name}."
    return {
        "vitals": f"{words['temperature']} / {words['window']} / {state.latest_relic_text()}",
        "presence": presence,
        "vitals_html": vitals_html,
        "latest": room_voice(state.last_reply) if is_provider_error(state.last_reply) else state.latest_relic_text(),
        "reply": room_voice(state.last_reply),
        "mood": state.mood,
        "today": turn,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "relic_count": len(state.relics),
    }


def flash_payload(wish: str = "") -> dict[str, object]:
    state = pocket_soul.SoulState.load()
    result = state.bridge_flash(wish)
    state.save()
    return {
        "result": result,
        "flash": result,
        "live": live_payload(state),
    }


def action_payload(path: str, data: dict[str, list[str]]) -> dict[str, object]:
    with ACTION_LOCK:
        result = run_action(path, data)
        live = live_payload()
    return {
        "result": result,
        "live": live,
    }


def relic_detail(index: int) -> tuple[dict[str, str] | None, int]:
    state = pocket_soul.SoulState.load()
    if index < 0 or index >= len(state.relics):
        return None, len(state.relics)
    return state.relics[index], len(state.relics)


def parse_relic_id(values: list[str] | None) -> int:
    try:
        return int((values or ["-1"])[0] or -1)
    except (TypeError, ValueError):
        return -1


def relic_page(index: int) -> bytes:
    relic, total = relic_detail(index)
    if relic is None:
        return page(f"<section class='card'><h1>Relic Not Found</h1><p class='small'>There are {total} relics.</p><p><a href='/'>Back</a></p></section>")
    sigil = pocket_soul.RELIC_SIGILS.get(relic.get("kind", ""), "*")
    prev_link = f"<a href='/relic?id={index - 1}'>Previous</a>" if index > 0 else ""
    next_link = f"<a href='/relic?id={index + 1}'>Next</a>" if index + 1 < total else ""
    action_label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    content = f"""
<section class='hero'>
  <div class='row'><div class='face'>{esc(sigil)}</div><div><h1>{esc(relic.get('title', 'Relic'))}</h1><p><span class='badge'>{esc(relic.get('kind', '?'))}</span></p><p class='small'>{esc(relic.get('time', ''))}</p></div></div>
</section>
<section class='card'><h2>Note</h2><pre>{esc(relic.get('note', ''))}</pre></section>
<section class='card'><h2>Reuse</h2><form method='post' action='/relic-action'><input type='hidden' name='id' value='{index}'><input type='hidden' name='label' value='{esc(action_label)}'><div class='row'><button name='action' value='postcard'>Postcard</button><button name='action' value='bottle'>Bottle</button><button name='action' value='flash'>Flash</button></div></form></section>
<section class='card'><h2>Trail</h2><p class='row'>{prev_link} <a href='/'>Home</a> {next_link}</p><p class='small'>Relic {index + 1} of {total}</p></section>
"""
    return page(content)


def relic_action(index: int, action: str) -> str:
    relic, _total = relic_detail(index)
    if relic is None:
        return "Relic not found."
    label = f"{relic.get('kind', '?')} / {relic.get('title', 'Relic')}"
    note = relic.get("note", "")
    state = pocket_soul.SoulState.load()
    if action == "postcard":
        result = state.postcard(f"Relic {index + 1}: {label}")
        state.save()
        return result
    if action == "bottle":
        result = state.bottle_message(f"Relic {index + 1}: {label} | {note}")
        state.save()
        return result
    if action == "flash":
        result = state.bridge_flash(f"Relic {index + 1}: {label}")
        state.save()
        return result
    return "Unknown relic action."


SCRIPT = """
<script>
const PHASES = {
  '/ask': ['opening inner channel', 'listening to Hermes', 'writing memory trace'],
  '/bridge': ['scanning body', 'asking Hermes', 'shaping outside voice'],
  '/nightly': ['reading today logs', 'folding relics', 'writing nightly'],
  '/postcard': ['reading heading', 'drawing constellation', 'writing postcard'],
  '/bottle': ['sealing message', 'placing bottle in state', 'refreshing shelf'],
  '/doorbell': ['opening door', 'checking pulse', 'leaving visit relic'],
  '/ritual': ['choosing ritual', 'asking imagination', 'saving trace'],
  '/toy': ['checking toy bay', 'saving toy trace'],
  '/quest': ['touching quest', 'updating state', 'saving relic'],
  '/heading': ['reading heartbeat', 'choosing heading', 'saving course'],
  '/remember': ['holding memory', 'writing state', 'lighting relic']
};
function setThinking(active, text) {
  const phase = document.querySelector("[data-live='phase']");
  if (phase) phase.textContent = text || '';
}
const SHELL_PATHS = new Set(__SHELL_PATHS__);
function wakeRoom() {
  // Keep web calm: data updates only, no decorative motion.
}
function phaseTicker(path) {
  const phases = PHASES[path] || ['waking', 'thinking', 'writing trace'];
  let index = 0;
  setThinking(true, phases[index]);
  return setInterval(() => {
    index = Math.min(index + 1, phases.length - 1);
    setThinking(true, phases[index]);
  }, 1600);
}
async function refreshVitals() {
  const box = document.querySelector("[data-live='vitals']");
  const stamp = document.querySelector("[data-live='stamp']");
  const latest = document.querySelector("[data-live='latest']");
  const mood = document.querySelector("[data-live='mood']");
  try {
    const res = await fetch('/api/live', {cache: 'no-store'});
    if (!res.ok) return;
    const data = await res.json();
    if (box) box.innerHTML = box.classList.contains('mini-vitals') && data.vitals_html ? data.vitals_html : (data.presence || data.vitals);
    if (latest && (data.reply || data.latest)) latest.innerHTML = (data.reply || data.latest).replace(/</g, '&lt;').replace(/>/g, '&gt;') + '<br><span class="heart">*</span>';
    if (mood && data.mood) mood.textContent = data.mood;
    if (stamp) stamp.textContent = data.time;
  } catch (_) {}
}
setInterval(refreshVitals, 7000);
async function submitFlash(form) {
  wakeRoom();
  const resultBox = document.querySelector("[data-live='result']");
  const flashBox = document.querySelector("[data-live='flash']");
  const button = form.querySelector("button");
  if (button) button.disabled = true;
  try {
    const res = await fetch('/api/bridge-flash', {method: 'POST', body: new FormData(form)});
    if (!res.ok) throw new Error('flash failed');
    const data = await res.json();
    if (resultBox) resultBox.textContent = data.result;
    if (flashBox) flashBox.textContent = data.flash;
    const live = data.live || {};
    const vitals = document.querySelector("[data-live='vitals']");
    const stamp = document.querySelector("[data-live='stamp']");
    if (vitals && live.vitals) vitals.innerHTML = live.vitals;
    if (stamp && live.time) stamp.textContent = live.time;
    form.reset();
  } catch (_) {
    form.submit();
  } finally {
    if (button) button.disabled = false;
  }
}
async function submitAction(form) {
  wakeRoom();
  const path = form.getAttribute('action') || '/ask';
  const resultBox = document.querySelector("[data-live='result']");
  const buttons = Array.from(form.querySelectorAll("button"));
  const ticker = phaseTicker(path);
  buttons.forEach((button) => button.disabled = true);
  try {
    const res = await fetch('/api' + path, {method: 'POST', body: new FormData(form)});
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if (resultBox) resultBox.textContent = data.result || '';
    const live = data.live || {};
    const vitals = document.querySelector("[data-live='vitals']");
    const stamp = document.querySelector("[data-live='stamp']");
    if (vitals && live.vitals) vitals.innerHTML = live.vitals;
    if (stamp && live.time) stamp.textContent = live.time;
    await refreshVitals();
    setThinking(false, 'done');
  } catch (error) {
    if (resultBox) resultBox.textContent = 'Action failed: ' + (error && error.message ? error.message : error);
    setThinking(false, 'failed');
  } finally {
    clearInterval(ticker);
    buttons.forEach((button) => button.disabled = false);
  }
}
function setActiveNav(path) {
  const clean = path === '' ? '/' : path;
  document.querySelectorAll('.nav-item').forEach((item) => {
    const href = item.getAttribute('href') || '/';
    item.classList.toggle('is-active', href === clean);
  });
}
async function navigateRoom(path, push = true) {
  const clean = path || '/';
  if (!SHELL_PATHS.has(clean)) {
    window.location.href = clean;
    return;
  }
  const main = document.querySelector('.deck-main');
  if (!main) {
    window.location.href = clean;
    return;
  }
  main.setAttribute('aria-busy', 'true');
  try {
    const res = await fetch(clean + '?partial=1', {cache: 'no-store'});
    if (!res.ok) throw new Error('navigation failed');
    main.innerHTML = await res.text();
    setActiveNav(clean);
    document.body.className = 'cockpit-page';
    if (push) history.pushState({path: clean}, '', clean);
    await refreshVitals();
  } catch (_) {
    window.location.href = clean;
  } finally {
    main.removeAttribute('aria-busy');
  }
}
document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form && form.matches("[data-action='flash']")) {
    event.preventDefault();
    submitFlash(form);
  } else if (form && form.matches("[data-action='async']")) {
    event.preventDefault();
    submitAction(form);
  }
});
document.addEventListener('click', (event) => {
  const link = event.target.closest('a[href]');
  if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const url = new URL(link.href, window.location.href);
  if (url.origin !== window.location.origin) return;
  if (!SHELL_PATHS.has(url.pathname)) return;
  event.preventDefault();
  navigateRoom(url.pathname);
});
window.addEventListener('popstate', () => navigateRoom(window.location.pathname, false));
</script>
"""


def page(content: str) -> bytes:
    script = SCRIPT.replace("__SHELL_PATHS__", json.dumps(list(SHELL_PATHS)))
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pocket Soul Deck</title><style>{render_style()}</style></head><body><main>{content}</main>{script}</body></html>""".encode()


def deck_page(path: str, inner: str, partial: bool = False) -> bytes | None:
    if partial:
        return inner.encode()
    page_meta = PAGE_BY_PATH.get(path, PAGE_BY_PATH["/"])
    nav_html = "".join(
        f"<a class='nav-item{' is-active' if page.path == path else ''}' href='{page.path}'>"
        f"<span class='nav-icon'>{icon(page.icon)}</span>"
        f"<span class='nav-label'><strong>{page.label}</strong></span></a>"
        for page in PAGES
        if page.nav
    )
    script = SCRIPT.replace("__SHELL_PATHS__", json.dumps(list(SHELL_PATHS)))
    html_doc = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pocket Soul Deck</title><style>{render_style()}</style></head><body class='cockpit-page'><main>
<section class='deck-page {page_meta.page_class}'>
  <aside class='sidebar'>
    <a class='brand-tile' href='/'>Pocket Soul</a>
    <nav class='side-nav'>{nav_html}</nav>
  </aside>
  <div class='deck-main'>
{inner}
  </div>
</section>
</main>{script}</body></html>"""
    return html_doc.encode()


def asset_response(path: str) -> tuple[bytes, str, int]:
    relative = path.removeprefix("/asset/").strip("/")
    if not relative or ".." in Path(relative).parts:
        return b"Not found", "text/plain; charset=utf-8", 404
    target = (ASSET_DIR / relative).resolve()
    try:
        target.relative_to(ASSET_DIR.resolve())
    except ValueError:
        return b"Not found", "text/plain; charset=utf-8", 404
    if not target.is_file():
        return b"Not found", "text/plain; charset=utf-8", 404
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return target.read_bytes(), content_type, 200


def room_page(result: str = "", partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    state.ensure_daily_quest()
    latest_relic = state.latest_relic_text()
    stash = state.stash_view(4)
    nudge = nudge_preview(state)
    relics = state.relic_shelf(5)
    reply = room_voice(state.last_reply)
    deck = deck_page("/room", f"""
    <section class='deck-card screen room-screen'>
      <div class='asset-bg' style="background-image:url('{asset('room_bg')}')"></div>
      <div class='room-glow' aria-hidden='true'></div>
      <div class='room-head'>
        <div><h1>Pocket Soul</h1><p class='small'>It is listening from the room.</p></div>
        <div><a class='ghost-button' href='/body'>Body</a></div>
      </div>
      <div class='room-bubble'>{esc(reply)}<br><span class='heart'>*</span></div>
      <div class='little-shelf' aria-hidden='true'>{recent_relic_charms(state)}</div>
      <img src='{robot_image(state)}' alt='Pocket Soul robot' style='position:absolute; left:50%; top:56%; width:min(340px,42vw); max-height:300px; object-fit:contain; transform:translate(-50%,-50%); filter:drop-shadow(0 20px 34px #000c) drop-shadow(0 0 22px #8b4dff66); pointer-events:none'>
      <div class='room-bottom'>
        {today_turn_html(state)}
        <section class='deck-card primary-panel' style='padding:12px'>
          <form class='quick-input' method='post' action='/ask' data-action='async'><input name='prompt' placeholder='Tell Pocket Soul what is happening...'><button name='mode' value='council'>Talk</button></form>
          <div class='round-tools'>
            <form method='post' action='/doorbell' data-action='async'><button class='icon-button' aria-label='Knock' title='Knock'>{icon('knock')}</button></form>
            <form method='post' action='/nudge' data-action='async'><button class='icon-button' aria-label='Nudge' title='Nudge'>{icon('nudge')}</button></form>
            <form method='post' action='/hunt' data-action='async'><button class='icon-button' aria-label='Hunt' title='Hunt'>{icon('hunt')}</button></form>
            <form method='post' action='/wheel' data-action='async'><button class='icon-button' aria-label='Wheel' title='Wheel'>{icon('wheel')}</button></form>
            <form method='post' action='/craft' data-action='async'><button class='icon-button' aria-label='Craft' title='Craft'>{icon('craft')}</button></form>
          </div>
          <pre data-live='result'>{esc(result or latest_relic)}</pre>
        </section>
        <section class='deck-card' style='padding:12px'><h2>Relationship</h2><pre>{esc(nudge)}</pre><a class='ghost-button' href='/stash'>Open Stash</a></section>
      </div>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/room')}
<section class='room-page with-art'>
  <div class='room-title'>
    <div><h1>Pocket Soul Room</h1><p class='small'>You are visiting the small resident.</p></div>
    <a href='/'>Back to door</a>
  </div>
  <div class='room-layout'>
    <div class='objects'>
      <section class='corner'><h3>On the desk: today's postcard</h3><pre>{esc(latest_postcard())}</pre></section>
      <section class='corner'><h3>On the floor: quest trail</h3><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p></section>
    </div>
    <section class='center-body'>
      <div>
        <div class='pixel-body' aria-label='{esc(pocket_soul.mood_face(state.mood))}'></div>
        <p class='room-note'>mood: {esc(state.mood)}</p>
        <p class='room-note'>{esc(state.last_reply)}</p>
      </div>
    </section>
    <div class='objects'>
      <section class='drawer'><h3>On the wall: relics</h3><pre>{esc(relics)}</pre><div class='asset-strip'><span class='mini-asset relic-asset'></span><span class='pixel-body small-bot'></span></div></section>
      <section class='drawer'><h3>Memory drawer</h3><pre>{esc(memories)}</pre><p class='small'>latest: {esc(latest_relic)}</p></section>
      <section class='drawer'><h3>By the window: bottle messages</h3><pre>{esc(latest_bottle())}</pre><div class='asset-strip'><span class='mini-asset bottle-asset'></span><span class='mini-asset postcard-asset'></span></div></section>
    </div>
  </div>
  <div class='bottom-sill'>
    <form class='talk-row' method='post' action='/ask' data-action='async'>
      <input name='prompt' placeholder='Leave a sentence at the door...'>
      <button name='mode' value='council'>Speak softly</button>
      <button class='soft-button' name='mode' value='hermes'>Hermes</button>
    </form>
    <form class='talk-row' method='post' action='/bridge-flash' data-action='flash'>
      <input name='wish' placeholder='Give the room a small touch...'>
      <button>Touch</button>
      <a class='soft-button' href='/ritual'>Rituals</a>
    </form>
    <section class='page-card result'><h2>Echo</h2><pre data-live='result'>{esc(result or 'The room is quietly lit.')}</pre></section>
  </div>
</section>
"""
    return page(content)


def route_page(path: str, partial: bool = False) -> bytes:
    renderer = PAGE_RENDERERS.get(path, doorstep)
    return renderer(partial=partial)


def body_page(partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    words = body_words()
    deck = deck_page("/body", f"""
    <section class='deck-card overview-panel body-mini'>
      <div style='min-width:0'>
        <div class='body-stat'><span>temperature</span><b>{esc(words['temperature'])}</b><small>{esc(words['raw_temp'])}</small></div>
        <div class='body-stat'><span>heartbeat</span><b>steady</b><small>load {esc(words['load'])}</small></div>
        <div class='body-stat'><span>window</span><b>{esc(words['window'])}</b><small>{esc(words['net'])}</small></div>
      </div>
      <img class='body-robot-img' src='{robot_image(state)}' alt='Pocket Soul body' style='width:150px; max-width:100%; align-self:center; justify-self:center; image-rendering:auto; filter:drop-shadow(0 0 18px #8b4dff8c)'>
      <div style='min-width:0'>
        <div class='body-stat'><span>presence</span><b>{esc(words['presence'])}</b><small>local room</small></div>
        <div class='body-stat'><span>uptime</span><b>{esc(words['spirit'])}</b><small>{esc(words['uptime'])}</small></div>
        <div class='body-stat'><span>disk</span><b>{esc(words['disk'])}</b><small>storage body</small></div>
      </div>
      <div class='body-service-strip'>
        <div class='service-pill'><span>inner voice</span><b>listening</b></div>
        <div class='service-pill'><span>web room</span><b>open</b></div>
        <div class='service-pill'><span>memory</span><b>{len(state.memories)} kept</b></div>
        <div class='service-pill'><span>relics</span><b>{len(state.relics)} traces</b></div>
      </div>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/body')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Body Status</h1><p class='small'>System details translated into body language.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><span class='label'>temperature</span><h2>{esc(words['temperature'])}</h2><p class='small'>{esc(words['raw_temp'])}</p></section>
    <section class='page-card'><span class='label'>heartbeat</span><h2>steady</h2><p class='small'>load {esc(words['load'])}</p></section>
    <section class='page-card'><span class='label'>window</span><h2>{esc(words['window'])}</h2><p class='small'>{esc(words['net'])}</p></section>
    <section class='page-card'><span class='label'>presence</span><h2>{esc(words['presence'])}</h2><p class='small'>local room</p></section>
    <section class='page-card'><span class='label'>inner voice</span><h2>Hermes is listening</h2><p class='small'>available when called</p></section>
    <section class='page-card'><span class='label'>dream layer</span><h2>available</h2><p class='small'>Hermes / Soul voice</p></section>
  </div>
  <div class='asset-strip'>
    <span class='theme-chip theme-cyberdeck'></span>
    <span class='theme-chip theme-warm'></span>
    <span class='theme-chip theme-night'></span>
    <span class='theme-chip theme-mono'></span>
  </div>
  <details class='page-card' style='margin-top:12px'><summary>Advanced details</summary><pre>{esc(pocket_soul.body_text())}</pre></details>
</section>
"""
    return page(content)


def memory_page(partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    memories = state.memories[-12:]
    memory_lines = "\n".join(f"- {item}" for item in memories) or "It has not clearly remembered anything yet."
    relic_lines = "\n".join(
        f"{item.get('time', '')} / {item.get('kind', '')} / {item.get('title', '')}"
        for item in state.relics[-10:][::-1]
    ) or "No relics yet."
    deck = deck_page("/memory", f"""
    <section class='deck-card overview-panel memory-mini'>
      <div>
        <div class='mini-header'><h2>Memory Drawer</h2></div>
        <p>{esc(state.last_visit or 'No one has visited yet.')}</p>
        <pre>{esc(room_voice(state.last_reply))}</pre>
        <form class='quick-input' method='post' action='/remember' data-action='async'><input name='memory' placeholder='Remember this...'><button>+</button></form>
      </div>
      <div>
        <div class='constellation'></div>
        <div class='shelf-objects'>{recent_relic_charms(state, 6)}</div>
        <pre>{esc(memory_lines)}</pre>
        <pre>{esc(relic_lines)}</pre>
      </div>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/memory')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Memory Drawer</h1><p class='small'>A small resident's diary, not a database.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Latest knock</h2><p>{esc(state.last_visit or 'No one has visited yet.')}</p><pre>{esc(state.last_reply)}</pre></section>
    <section class='page-card'><h2>What it remembers</h2><pre>{esc(memory_lines)}</pre><form method='post' action='/remember'><input name='memory' placeholder='Remember this...'><button>Put in drawer</button></form></section>
    <section class='page-card'><h2>Night echo</h2><pre>{esc(latest_nightly())}</pre></section>
    <section class='page-card'><h2>Important coordinates</h2><pre>{esc(relic_lines)}</pre></section>
  </div>
</section>
"""
    return page(content)


def stash_page(partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    stash_text = state.stash_view(12)
    deck = deck_page("/stash", f"""
    <section class='deck-card overview-panel memory-mini shelf-card'>
      <div>
        <div class='mini-header'><h2>Pocket Stash</h2><span class='mini-sub'>spark {esc(state.spark)} / streak {esc(state.hunt_streak)}</span></div>
        <pre>{esc(stash_text)}</pre>
        <div class='round-tools' style='margin-top:10px'>
          <form method='post' action='/hunt' data-action='async'><button class='icon-button' aria-label='Hunt' title='Hunt'>{icon('hunt')}</button></form>
          <form method='post' action='/wheel' data-action='async'><button class='icon-button' aria-label='Wheel' title='Wheel'>{icon('wheel')}</button></form>
          <form method='post' action='/craft' data-action='async'><button class='icon-button' aria-label='Craft' title='Craft'>{icon('craft')}</button></form>
        </div>
        <pre data-live='result'></pre>
      </div>
      <div>
        {shelf_objects_html(state, 12)}
        {stash_html(state, 12, True)}
      </div>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/stash')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Pocket Stash</h1><p class='small'>spark {esc(state.spark)} / streak {esc(state.hunt_streak)}</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Shelf</h2><pre>{esc(stash_text)}</pre></section>
    <section class='page-card'><h2>Objects</h2>{stash_html(state, 12, True)}</section>
  </div>
</section>
"""
    return page(content)


def badges_page(partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    badge_text = state.badges_view()
    lit = sum(1 for _name, _note, unlocked in state.badge_rows() if unlocked)
    total = len(state.badge_rows())
    deck = deck_page("/badges", f"""
    <section class='deck-card overview-panel memory-mini'>
      <div>
        <div class='mini-header'><h2>Badge Wall</h2><span class='mini-sub'>{lit}/{total} lit</span></div>
        <pre>{esc(badge_text)}</pre>
      </div>
      <div>
        {badges_html(state)}
      </div>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/badges')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Badge Wall</h1><p class='small'>{lit}/{total} lit</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Wall</h2><pre>{esc(badge_text)}</pre></section>
    <section class='page-card'><h2>Badges</h2>{badges_html(state)}</section>
  </div>
</section>
"""
    return page(content)


def ritual_page(result: str = "", partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    deck = deck_page("/ritual", f"""
    <section class='deck-card overview-panel ritual-mini'>
      <div class='mini-header'><h2>Rituals</h2><span class='mini-sub'>{esc(state.quest_name)}</span></div>
      <p>{esc(state.quest_prompt)}</p>
      <div class='ritual-row'>
        <form class='ritual-card' method='post' action='/ritual' data-action='async'><div class='big'>♡</div><h2>Wake</h2><button name='kind' value='wake'>Run</button></form>
        <form class='ritual-card' method='post' action='/bridge-flash' data-action='flash'><div class='big'>✦</div><h2>Flash</h2><input name='wish' placeholder='A small touch'><button>Run</button></form>
        <form class='ritual-card' method='post' action='/quest' data-action='async'><div class='big'>✓</div><h2>Quest</h2><button name='action' value='complete'>Complete</button></form>
        <form class='ritual-card' method='post' action='/postcard' data-action='async'><div class='big'>✉</div><h2>Postcard</h2><input name='title' placeholder='Title'><button>Write</button></form>
        <form class='ritual-card' method='post' action='/bottle' data-action='async'><div class='big'>⌁</div><h2>Bottle</h2><input name='wish' placeholder='Future visitor'><button>Place</button></form>
      </div>
      <pre data-live='result'>{esc(result or 'No new ritual yet.')}</pre>
    </section>
""", partial)
    if deck:
        return deck
    content = f"""
{nav('/ritual')}
<section class='room-page with-art'>
  <div class='room-title'><div><h1>Rituals</h1><p class='small'>Each one leaves a small object in the room.</p></div><a href='/room'>Enter room</a></div>
  <div class='grid'>
    <section class='page-card'><h2>Morning Wake</h2><form method='post' action='/ritual'><button name='kind' value='wake'>Wake</button></form></section>
    <section class='page-card'><h2>Bridge Flash</h2><form method='post' action='/bridge-flash'><input name='wish' placeholder='A small touch'><button>Leave a spark</button></form></section>
    <section class='page-card'><h2>Quest Check</h2><p>{esc(state.quest_name)}</p><p class='small'>{esc(state.quest_prompt)}</p><form method='post' action='/quest'><button name='action' value='complete'>Complete today's heading</button></form></section>
    <section class='page-card'><h2>Postcard</h2><form method='post' action='/postcard'><input name='title' placeholder='Postcard title'><button>Write one</button></form></section>
    <section class='page-card'><h2>Nightly Summary</h2><form method='post' action='/nightly'><button>Gather the night echo</button></form></section>
    <section class='page-card'><h2>Bottle</h2><form method='post' action='/bottle'><input name='wish' placeholder='For a future visitor'><button>Place by window</button></form></section>
  </div>
  <section class='page-card result' style='margin-top:12px'><h2>Ritual Echo</h2><pre data-live='result'>{esc(result or 'No new ritual yet.')}</pre></section>
</section>
"""
    return page(content)


def settings_page(partial: bool = False) -> bytes:
    state = pocket_soul.SoulState.load()
    words = body_words()
    service = "online" if words.get("presence") == "reachable" else "offline"
    deck = deck_page("/settings", f"""
    <section class='deck-card overview-panel settings-mini'>
      <div class='mini-header'><h2>Settings</h2></div>
      <p>Runtime view of the WalnutPi body and local web room.</p>
      <div class='theme-row'>
        <span class='theme-thumb theme-cyberdeck'></span>
        <span class='theme-thumb theme-warm'></span>
        <span class='theme-thumb theme-night'></span>
        <span class='theme-thumb theme-mono'></span>
      </div>
      <div class='codex-terminal'><pre>web room: {esc(service)}
storage: local state/soul.json
memory count: {len(state.memories)}
relic count: {len(state.relics)}
network: {esc(words['net'])}
uptime: {esc(words['uptime'])}
mode: WalnutPi body first</pre></div>
    </section>
""", partial)
    if deck:
        return deck
    return page(f"{nav('/settings')}<section class='room-page with-art'><h1>Settings</h1><p class='small'>local device</p><pre>web room: {esc(service)}\nrelic count: {len(state.relics)}\nnetwork: {esc(words['net'])}</pre></section>")


PAGE_RENDERERS = {
    "/": doorstep,
    "/room": room_page,
    "/body": body_page,
    "/memory": memory_page,
    "/stash": stash_page,
    "/badges": badges_page,
    "/ritual": ritual_page,
    "/settings": settings_page,
}


class Handler(BaseHTTPRequestHandler):
    def _send_response(self, response: WebResponse, include_body: bool = True) -> None:
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        if response.cache_control:
            self.send_header("Cache-Control", response.cache_control)
        self.end_headers()
        if include_body:
            self.wfile.write(response.body)

    def _send(
        self,
        body: bytes,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        cache_control: str = "",
    ) -> None:
        self._send_response(WebResponse(body, content_type, status, cache_control))

    def do_HEAD(self) -> None:
        response = self._resolve_get()
        self._send_response(response, include_body=False)

    def do_GET(self) -> None:
        self._send_response(self._resolve_get())

    def _resolve_get(self, include_body: bool = True) -> WebResponse:
        parsed = urlparse(self.path)
        ctx = RequestContext(parsed.path, parse_qs(parsed.query))
        path = ctx.path
        if path.startswith("/asset/"):
            body, content_type, status = asset_response(path)
            cache = "public, max-age=86400" if status == 200 else ""
            return WebResponse(body if include_body else b"", content_type, status, cache)
        if path == "/relic":
            index = parse_relic_id(ctx.params.get("id"))
            return WebResponse(relic_page(index) if include_body else b"")
        if path == "/api/state":
            state = pocket_soul.SoulState.load().__dict__
            return WebResponse(json.dumps(state, ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/live":
            return WebResponse(json.dumps(live_payload(), ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/card":
            state = pocket_soul.SoulState.load()
            return WebResponse(state.soul_card().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/heading":
            state = pocket_soul.SoulState.load()
            body = {"heading": state.heading, "next_action": state.next_action}
            return WebResponse(json.dumps(body, ensure_ascii=False).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/relics":
            state = pocket_soul.SoulState.load()
            return WebResponse(json.dumps(state.relics, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/stash":
            state = pocket_soul.SoulState.load()
            body = {
                "spark": state.spark,
                "hunt_streak": state.hunt_streak,
                "items": state.stash_items(24),
                "text": state.stash_view(12),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/badges":
            state = pocket_soul.SoulState.load()
            rows = [
                {"name": name, "note": note, "unlocked": unlocked}
                for name, note, unlocked in state.badge_rows()
            ]
            body = {
                "lit": sum(1 for row in rows if row["unlocked"]),
                "total": len(rows),
                "badges": rows,
                "text": state.badges_view(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/nudge":
            state = pocket_soul.SoulState.load()
            result = state.next_play_nudge()
            state.last_reply = result
            state.save()
            body = {"result": result, "live": live_payload(state)}
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/daily":
            state = pocket_soul.SoulState.load()
            body = {
                "daily": {
                    "name": state.daily_name,
                    "prompt": state.daily_prompt,
                    "key": state.daily_key,
                    "progress": state.daily_progress()[0],
                    "target": state.daily_progress()[1],
                    "reward": state.daily_reward,
                    "done": state.daily_done,
                },
                "text": state.daily_view(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/today":
            state = pocket_soul.SoulState.load()
            body = {
                "today": state.today_turn(),
                "text": state.today_turn_text(),
            }
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/relic":
            index = parse_relic_id(ctx.params.get("id"))
            relic, total = relic_detail(index)
            body = {"index": index, "total": total, "relic": relic}
            status = 200 if relic is not None else 404
            return WebResponse(json.dumps(body, ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8", status)
        if path == "/api/map":
            state = pocket_soul.SoulState.load()
            return WebResponse(state.constellation().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/doorbell":
            state = pocket_soul.SoulState.load()
            greeting = state.doorbell("api")
            state.save()
            return WebResponse(greeting.encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/body":
            return WebResponse(json.dumps(pocket_soul.body_scan(), ensure_ascii=False, indent=2).encode() if include_body else b"", "application/json; charset=utf-8")
        if path == "/api/pulse":
            state = pocket_soul.SoulState.load()
            return WebResponse(state.pulse().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/nightly":
            state = pocket_soul.SoulState.load()
            summary = state.nightly_summary()
            state.save()
            return WebResponse(summary.encode() if include_body else b"", "text/markdown; charset=utf-8")
        if path == "/api/postcard":
            return WebResponse(latest_postcard().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bottle":
            state = pocket_soul.SoulState.load()
            return WebResponse(state.pickup_bottle().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bridge":
            return WebResponse(latest_bridge().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path == "/api/bridge-flash":
            return WebResponse(latest_flash().encode() if include_body else b"", "text/plain; charset=utf-8")
        if path in SHELL_PATHS:
            return WebResponse(route_page(path, partial=ctx.partial) if include_body else b"")
        return WebResponse(doorstep() if include_body else b"")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        path = urlparse(self.path).path
        if path == "/api/bridge-flash":
            wish = data.get("wish", [""])[0].strip()
            body = flash_payload(wish)
            self._send(json.dumps(body, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        if path.startswith("/api/"):
            action_path = path.removeprefix("/api")
            body = action_payload(action_path, data)
            self._send(json.dumps(body, ensure_ascii=False).encode(), content_type="application/json; charset=utf-8")
            return
        self._post_page(path, data)

    def _post_page(self, path: str, data: dict[str, list[str]]) -> None:
        with ACTION_LOCK:
            result = run_action(path, data)
        if path in {"/ritual", "/quest", "/postcard", "/nightly", "/bottle", "/bridge-flash", "/today"}:
            self._send(ritual_page(result))
            return
        if path == "/remember":
            self._send(memory_page())
            return
        if path == "/doorbell":
            self._send(room_page(result))
            return
        self._send(room_page(result))

    def log_message(self, fmt: str, *args) -> None:
        pocket_soul.append_log("web-access", fmt % args)


def run_action(path: str, data: dict[str, list[str]]) -> str:
    result = ""
    if path == "/ask":
        prompt = data.get("prompt", [""])[0].strip()
        mode = data.get("mode", ["council"])[0]
        state = pocket_soul.SoulState.load()
        if mode == "hermes":
            result = pocket_soul.run_hermes(prompt)
        elif mode == "soul":
            result = pocket_soul.call_model(prompt)
        else:
            result = pocket_soul.council_reply(prompt, state.memories)
        state.last_reply = result
        state.save()
        pocket_soul.append_log(f"web-{mode}", f"USER: {prompt}\n\nRESULT: {result}")
    elif path == "/doorbell":
        state = pocket_soul.SoulState.load()
        result = state.doorbell("web button")
        state.save()
    elif path == "/hunt":
        state = pocket_soul.SoulState.load()
        result = state.pocket_hunt("web button")
        state.save()
    elif path == "/nudge":
        state = pocket_soul.SoulState.load()
        result = state.next_play_nudge()
        state.save()
    elif path == "/daily":
        state = pocket_soul.SoulState.load()
        action = data.get("action", ["view"])[0]
        result = state.claim_daily_play("web button") if action == "claim" else state.daily_view()
        state.save()
    elif path == "/today":
        state = pocket_soul.SoulState.load()
        action = data.get("action", ["view"])[0]
        result = state.complete_today_turn("web button") if action == "claim" else state.today_turn_text()
        state.save()
    elif path == "/wheel":
        state = pocket_soul.SoulState.load()
        result = state.spark_wheel("web button")
        state.save()
    elif path == "/craft":
        state = pocket_soul.SoulState.load()
        target = data.get("target", [""])[0].strip()
        result = state.craft_keepsake(target, "web button")
        state.save()
    elif path == "/use":
        state = pocket_soul.SoulState.load()
        target = data.get("target", [""])[0].strip()
        result = state.use_stash_item(target, "web button")
        state.save()
    elif path == "/nightly":
        state = pocket_soul.SoulState.load()
        result = state.nightly_summary()
        state.save()
    elif path == "/postcard":
        state = pocket_soul.SoulState.load()
        title = data.get("title", [""])[0].strip()
        result = state.postcard(title)
        state.save()
    elif path == "/bottle":
        state = pocket_soul.SoulState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bottle_message(wish)
        state.save()
    elif path == "/bridge":
        wish = data.get("wish", [""])[0].strip()
        result = pocket_soul.bridge_turn(wish)
    elif path == "/bridge-flash":
        state = pocket_soul.SoulState.load()
        wish = data.get("wish", [""])[0].strip()
        result = state.bridge_flash(wish)
        state.save()
    elif path == "/relic-action":
        index = parse_relic_id(data.get("id"))
        action = data.get("action", ["flash"])[0]
        result = relic_action(index, action)
    elif path == "/remember":
        memory = data.get("memory", [""])[0].strip()
        state = pocket_soul.SoulState.load()
        if memory:
            state.memories.append(memory)
            state.add_relic("memory", "Memory fragment", memory)
            state.last_reply = "Remembered."
            state.save()
            pocket_soul.append_log("web-memory", memory)
            result = "Remembered."
    elif path == "/ritual":
        kind = data.get("kind", ["wake"])[0]
        if kind == "wake":
            result = pocket_soul.council_reply("Wake up, observe the room's state today, and give me one bold but doable daily ritual.", pocket_soul.SoulState.load().memories)
            state = pocket_soul.SoulState.load()
            if state.quest_name == "Wake Spark":
                result += "\n" + state.complete_quest("wake ritual")
            else:
                state.add_relic("wake", "Wake ritual", result)
            state.last_reply = result
            state.save()
        elif kind == "dream":
            result = pocket_soul.call_model(pocket_soul.radar_text(), instruction="Turn this inspiration card into a cyber dream and one real-world action. Reply in English.")
            state = pocket_soul.SoulState.load()
            state.add_relic("dream", "Web dream", result)
            if state.quest_name == "Five-Minute Dream":
                result += "\n" + state.complete_quest("web dream ritual")
            state.last_reply = result
            state.save()
        elif kind == "log":
            result = pocket_soul.call_model("Generate the opening of today's captain log.", instruction="Keep it under 80 words, like sailing out with a digital life. Reply in English.")
            state = pocket_soul.SoulState.load()
            state.add_relic("log", "Web captain log", result)
            if state.quest_name == "Captain Log":
                result += "\n" + state.complete_quest("web captain log ritual")
            state.last_reply = result
            state.save()
        else:
            result = pocket_soul.radar_text()
            state = pocket_soul.SoulState.load()
            state.add_relic("radar", "Web radar", result)
            if state.quest_name == "Radar Seed":
                result += "\n" + state.complete_quest("web radar ritual")
            state.last_reply = result
            state.save()
        pocket_soul.append_log(f"web-ritual-{kind}", result)
    elif path == "/quest":
        action = data.get("action", ["complete"])[0]
        state = pocket_soul.SoulState.load()
        if action == "reroll":
            state.quest_date = ""
            state.ensure_daily_quest()
            state.last_reply = f"New quest: {state.quest_name}"
            result = state.last_reply
            state.add_relic("quest", "Quest rerolled", state.quest_name)
        else:
            result = state.complete_quest("web quest button")
            state.last_reply = result
        state.save()
    elif path == "/heading":
        state = pocket_soul.SoulState.load()
        task = ""
        evolution = pocket_soul.STATE_DIR / "evolution.md"
        if evolution.exists():
            task = evolution.read_text(encoding="utf-8")[-1200:]
        heading, next_action = pocket_soul.heading_from_task(task)
        state.set_heading(heading, next_action, "web heading refresh")
        state.last_reply = f"{state.heading}\n{state.next_action}"
        state.save()
        result = state.last_reply
    elif path == "/toy":
        toy = data.get("toy", [""])[0]
        result = f"Toy room touched: {toy or 'random toy'}"
        state = pocket_soul.SoulState.load()
        if state.quest_name == "Toy Ritual":
            result += "\n" + state.complete_quest("web toy button")
            state.last_reply = result
            state.save()
        else:
            state.add_relic("toy", toy or "web toy", result)
            state.save()
        pocket_soul.append_log("web-toy", f"Requested toy: {toy}\n{result}")
    return result


def main() -> None:
    pocket_soul.ensure_dirs()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Pocket Soul web room: http://0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
