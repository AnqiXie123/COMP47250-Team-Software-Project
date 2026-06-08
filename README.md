# EcoCharge Dublin: Data-Driven Dashboard

An interactive urban planning and decision-support system designed to optimize EV charging infrastructure and renewable energy integration across Dublin.

##  Frontend Deployment (Sprint 1 MVP)

The interactive map application has been successfully deployed and is live for testing:
**[Click Here to Open Live Dashboard](https://github.com/AnqiXie123/COMP47250-Team-Software-Projec/blob/frontend/index.html)**

---

##  Implemented Features (This Week)

- **Interactive Base Maps**: Switched the default viewport to **Standard Map** and integrated a highly stylized **Dark Mode Map** as a mutually exclusive option.
- **Geospatial Point Optimization**: Implemented custom geospatial deduplication logic to ensure precise coordination and layout overlays for redundant anchor markers.
- **Dynamic Layer Controls**: Bound brand networks (`ESB Networks`, `EasyGo Networks`, and `Other Networks`) inside `<FeatureGroup>` structures to lock down right-panel UI toggles cleanly.
- **Rich Metric Popups**: Standardized localized English popups with brand-specific badge styling, live charger counts, and interactive analytics shortcuts.
