# LoGEM Edge

**Log GenAI Model powered by LLM to parse and forward logs on the edge.**

LoGEM Edge is a lightweight, local-first log parser built on LLM technology. It helps Security Operations (SOC) and content engineering teams extract meaningful insights from noisy logs and forward them securely in common formats like CEF, Syslog, and JSON.

---

## Features

- LLM-Powered Parsing: Extract key fields using templated GenAI prompts.
- Multi-Format Input: Supports EVTX, JSON, CSV, Sysmon, Registry, and more.
- Flexible Output: Converts logs to CEF, Syslog, or JSON.
- Secure Forwarding: Sends logs to remote SIEMs over TLS.
- GUI & CLI Modes: Simple UI for selection, or full CLI control.
- Template Tuner: Customize how logs are parsed and mapped.
- Granular Routing: Select which logs go to which receivers.

---

## Supported Platforms

- Windows (10/11/Server)  
- Linux (Debian/Ubuntu/CentOS)

---

## Output Formats

- Common Event Format (CEF)
- Syslog (RFC-compliant)
- JSON (flat or structured)

---

## Roadmap

- [ ] Lightweight embedded LLM model (Phi-2 / TinyLlama)
- [ ] Templates Tuner GUI tab
- [ ] Receiver Manager
- [ ] Auto log path discovery (OS-aware)
- [ ] CLI mode full support

---

## Project Structure

