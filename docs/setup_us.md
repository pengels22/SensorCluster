# US Deployment Notes

This document outlines safe power usage, hardware standards, and general best practices for deploying the SensorCluster system in the United States.

---

## ⚡ Power Requirements

- The device should be powered with a **USB-C power adapter**.
- Adapter specifications:
  - Input: 120V AC @ 60Hz (standard in the U.S.)
  - Output: 5V DC via USB-C, minimum 3A
  - Must be **UL-listed** (Underwriters Laboratories) for safety
  - Avoid gas station chargers and off-brand USB adapters

---

## 🔋 Battery Safety

- The system uses 3.7V lithium-ion batteries (approx. 10,000 mAh each).
- Always use protected lithium cells with:
  - Over-discharge and over-current protection
  - Built-in thermal cutoff
- Do not use swollen, damaged, or unbranded battery packs.
- Charging modules should support load-sharing and be UL-rated if possible.

---

## 🔌 Power Strip / Wall Adapter Guidance

- Use surge-protected power strips when connecting to mains.
- Avoid daisy-chaining multiple adapters.
- Ensure USB-C cable is thick gauge and not damaged or frayed.

---

## 📡 Wi-Fi and Connectivity

- Wi-Fi (802.11n) is legal and unlicensed in the U.S. under FCC Part 15.
- No special setup needed unless operating in a restricted RF environment.
- Tailscale is allowed and secure for domestic remote access.

---

## 📦 Physical Handling and Environment

- Ideal use is indoors in dry, ventilated spaces.
- If using outdoors or in garages/labs, enclose unit in plastic or sealed housing.
- Keep electronics away from heat, grease, pets, and children.

---

## 🛡️ System Tips for Smooth Operation

- Avoid unplugging the Pi while it’s writing logs or flashing firmware.
- If unit is frozen, press and hold the power button for a full reset.
- Use only USB-C adapters with a 3A+ current rating.
- For best results, plug directly into a wall outlet rather than a shared power bar.

---

## 🔄 Optional Labeling

- You may optionally mark units:
  - “Made in the USA”
  - Include emergency contact phone or URL inside enclosure lid

---

## 📝 Support Notes

This device is built for technically-inclined users. If shipping to general consumers:
- Include printed power/safety instructions
- Label ports clearly
- Include a support QR code linking to instructions

---

