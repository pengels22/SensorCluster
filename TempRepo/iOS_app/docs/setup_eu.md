# EU Deployment Notes

This document outlines safety, power, and hardware compliance considerations for deploying the SensorCluster system in European environments.

---

## ⚡ Power Requirements

- **Input Power**: The device must be powered using a **USB-C compliant power adapter**.
- Adapters must:
  - Support **230V AC @ 50Hz** (standard in EU countries)
  - Output **5V DC via USB-C**, minimum **3A current capacity**
  - Be **CE-certified** and built to **IEC 60950-1** or **EN 62368-1** standards
- Avoid using unregulated or unbranded USB-C power supplies.

---

## 🔋 Battery Safety

- The system uses **3.7V lithium-ion batteries** with a capacity of ~10,000 mAh.
- Batteries must include:
  - Overcharge protection
  - Over-discharge protection
  - Short-circuit and thermal protection
- Charging modules must be CE-rated and support simultaneous charge/discharge.

---

## 🧯 Enclosure and Materials

- Use **UL94 V-0 flame-retardant plastics** for enclosures.
- If using metal enclosures:
  - Include grounding to prevent ESD buildup
  - Isolate high-voltage sections from user-accessible areas

---

## 🧪 Cable and Connector Standards

- All power and signal cables must be **CE-compliant**.
- Signal lines should use shielded cables if passing through noisy environments.
- For power lines:
  - Use **0.75 mm² or larger** conductors if current exceeds 500 mA.
  - Use labeled connectors where required (e.g. JST, USB-C, XT60).

---

## 📡 Wi-Fi and Communication

- Wi-Fi communication (802.11n) must comply with **EN 300 328**.
- The device should not emit or receive outside of the 2.4 GHz band unless licensed.
- Tailscale tunnels are encrypted and compliant with EU privacy guidelines, but network traffic should still be audited for compliance.

---

## 🏷️ Labeling and Export Readiness

- Units intended for external deployment or distribution should include:
  - "Designed and assembled in the EU"
  - **CE marking** only if verified for full electrical and EMC compliance
- A product datasheet should accompany each shipment if required by the recipient.

---

## 🔒 Recommended Practices

- Verify insulation between battery, signal, and logic sections
- Avoid high-voltage traces on exposed PCBs
- Keep analog sensors away from DC-DC converters or inductive loads

---
