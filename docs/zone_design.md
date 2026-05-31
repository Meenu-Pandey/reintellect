# Zone Design Specification

## Objective

Define all virtual detection zones used by the ReIntellect analytics platform.

Zones are used for:

* Visitor tracking
* Dwell analysis
* Queue monitoring
* Conversion funnel analytics
* Security monitoring

---

# Camera Zone Mapping

## CAM1 – Checkout / POS

### ZONE_QUEUE

Purpose:

* Detect customers waiting for checkout

Events:

* QUEUE_JOIN
* QUEUE_LEAVE
* QUEUE_ABANDON

Metrics:

* Queue Length
* Average Wait Time
* Queue Abandonment Rate

---

### ZONE_POS

Purpose:

* Detect active checkout interactions

Events:

* POS_INTERACTION_START
* POS_INTERACTION_END

Metrics:

* Checkout Duration
* Active POS Sessions

---

### ZONE_CASHIER

Purpose:

* Detect cashier presence

Events:

* CASHIER_PRESENT
* CASHIER_ABSENT

Metrics:

* POS Utilization
* Unattended Checkout Alerts

---

# CAM2 – Makeup Zone

### ZONE_MAYBELLINE

Purpose:

Track customer engagement with Maybelline products.

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_FACES_CANADA

Purpose:

Track customer engagement with Faces Canada products.

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_LAKME

Purpose:

Track customer engagement with Lakme products.

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_SWISS_BEAUTY

Purpose:

Track customer engagement with Swiss Beauty products.

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

# CAM3 – Entrance

### ZONE_ENTRY

Purpose:

Count incoming visitors.

Events:

* VISITOR_ENTER

---

### ZONE_EXIT

Purpose:

Count outgoing visitors.

Events:

* VISITOR_EXIT

---

# CAM4 – Backroom

### ZONE_BACKROOM

Purpose:

Monitor restricted access.

Events:

* RESTRICTED_ACCESS
* AFTER_HOURS_ACTIVITY

---

### ZONE_STORAGE

Purpose:

Monitor inventory area activity.

Events:

* STOCKROOM_ACTIVITY

---

# CAM5 – Skincare Zone

### ZONE_FACE_SHOP

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_GOOD_VIBES

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_DERMA_CO

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_MINIMALIST

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

### ZONE_CENTRAL_DISPLAY

Events:

* ZONE_ENTER
* ZONE_EXIT
* DWELL

---

# Visitor Journey Funnel

Expected Visitor Flow

VISITOR_ENTER
→ MAKEUP_ZONE
→ SKINCARE_ZONE
→ CHECKOUT_QUEUE
→ POS_INTERACTION
→ VISITOR_EXIT

This funnel will be used to calculate conversion analytics.

---

# Future Polygon Storage

Each zone will eventually contain:

* zone_id
* camera_id
* polygon_points

Polygon coordinates will be defined during implementation using the actual store layout.
