/**
 * RentEase Client Interaction Suite
 * Modals, AJAX Bookings, Token Advance Payments, Photo Galleries, and WhatsApp Integration.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Mobile Nav Drawer Toggle
  const mobileToggle = document.getElementById("mobileMenuBtn");
  const mobileNav = document.getElementById("mobileNav");

  if (mobileToggle && mobileNav) {
    mobileToggle.addEventListener("click", () => {
      mobileNav.classList.toggle("open");
    });
  }

  // Close modals on Escape key or backdrop click
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeBookingModal();
      closeGalleryModal();
      closePaymentModal();
      closeReceiptModal();
      const profileModal = document.getElementById("profileModal");
      if (profileModal) profileModal.classList.add("hidden");
      const addListingModal = document.getElementById("addListingModal");
      if (addListingModal) addListingModal.classList.add("hidden");
    }
  });

  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.add("hidden");
      }
    });
  });

  // Pre-fill tomorrow's date for visit booking by default
  const visitDateInput = document.getElementById("visit_date");
  if (visitDateInput && !visitDateInput.value) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const yyyy = tomorrow.getFullYear();
    const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const dd = String(tomorrow.getDate()).padStart(2, '0');
    visitDateInput.value = `${yyyy}-${mm}-${dd}`;
    visitDateInput.min = `${yyyy}-${mm}-${dd}`;
  }

  // ─────────────────────────────────────────────────────────────
  // APPLE-STYLE SCROLL ANIMATIONS — IntersectionObserver Engine
  // ─────────────────────────────────────────────────────────────
  initScrollAnimations();
});

/**
 * Apple-style scroll reveal system.
 * Auto-assigns animation classes to all major UI elements,
 * then triggers them via IntersectionObserver as they enter the viewport.
 */
function initScrollAnimations() {

  // Skip if user prefers reduced motion
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  // ── 1. Auto-assign reveal classes to elements ──────────────────

  // Section badges & eyebrow labels → fade in
  document.querySelectorAll(".section-badge, .hero-pill, .auth-badge").forEach(el => {
    el.classList.add("reveal-fade");
  });

  // Main section headings → slide up
  document.querySelectorAll(
    ".hero-copy h1, section h2, .section-head h2, .auth-header h2, .dash-title"
  ).forEach(el => {
    el.classList.add("reveal");
  });

  // Hero subtext & description paragraphs → slide up with small delay
  document.querySelectorAll(
    ".hero-sub, .hero-actions-simple, .hero-search-box, .tally"
  ).forEach(el => {
    el.classList.add("reveal");
    el.classList.add("reveal-delay-1");
  });

  // Hero visual card → scale in from right
  document.querySelectorAll(".hero-visual-card").forEach(el => {
    el.classList.add("reveal-scale");
    el.classList.add("reveal-delay-2");
  });

  // Steps (How It Works) → staggered slide up
  document.querySelectorAll(".step").forEach((el, i) => {
    el.classList.add("reveal");
    el.classList.add(`reveal-delay-${Math.min(i + 1, 6)}`);
  });

  // Room cards → staggered scale-in
  document.querySelectorAll(".room-card, .listing-card").forEach((el, i) => {
    el.classList.add("reveal-scale");
    el.classList.add(`reveal-delay-${Math.min((i % 3) + 1, 6)}`);
  });

  // Roommate teaser section → split left/right
  const teaserContent = document.querySelector(".teaser-content");
  const teaserGraphic = document.querySelector(".teaser-graphic");
  if (teaserContent) teaserContent.classList.add("reveal-left");
  if (teaserGraphic) teaserGraphic.classList.add("reveal-right");

  // Teaser actions button → fade
  document.querySelectorAll(".teaser-actions, .section-head a.text-link").forEach(el => {
    el.classList.add("reveal-fade");
  });

  // Footer → gentle fade
  document.querySelectorAll(
    ".footer-brand-col, .footer-col, .footer-bottom"
  ).forEach((el, i) => {
    el.classList.add("reveal");
    el.classList.add(`reveal-delay-${Math.min(i + 1, 6)}`);
  });

  // Dashboard / admin cards → staggered
  document.querySelectorAll(
    ".metric-card, .dash-card, .admin-metric-card, .booking-row, .payment-row, .roommate-card"
  ).forEach((el, i) => {
    el.classList.add("reveal");
    el.classList.add(`reveal-delay-${Math.min((i % 4) + 1, 6)}`);
  });

  // Auth / form panels → slide up
  document.querySelectorAll(
    ".auth-card, .form-card, .filter-card"
  ).forEach(el => {
    el.classList.add("reveal");
  });

  // Section dividers / "How it works" label → fade
  document.querySelectorAll(".how .section-badge, .listings-preview .section-badge").forEach(el => {
    el.classList.add("reveal-fade");
  });

  // ── 2. IntersectionObserver — fires when element enters viewport ──

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          // Un-observe after animation so it only plays once
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.12,        // trigger when 12% of element is visible
      rootMargin: "0px 0px -40px 0px"  // slightly before bottom edge
    }
  );

  // Observe all animated elements
  document.querySelectorAll(
    ".reveal, .reveal-fade, .reveal-scale, .reveal-left, .reveal-right"
  ).forEach(el => observer.observe(el));
}

// -----------------------------------------------------------------------------
// Booking Modal Controller
// -----------------------------------------------------------------------------

function openBookingModal(listingId, name, area, rent) {
  const modal = document.getElementById("bookingModal");
  const titleEl = document.getElementById("modalListingTitle");
  const areaEl = document.getElementById("modalListingArea");
  const idInput = document.getElementById("bookingListingId");

  if (titleEl) titleEl.textContent = `Schedule Visit: ${name}`;
  if (areaEl) areaEl.textContent = `📍 ${area} • ₹${Number(rent).toLocaleString()}/month`;
  if (idInput) idInput.value = listingId;

  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeBookingModal() {
  const modal = document.getElementById("bookingModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

async function submitVisitBooking(event) {
  event.preventDefault();
  const btn = document.getElementById("btnConfirmBooking");
  const originalText = btn ? btn.textContent : "Confirm";

  if (btn) {
    btn.disabled = true;
    btn.textContent = "Reserving Slot...";
  }

  const listingId = document.getElementById("bookingListingId").value;
  const visitDate = document.getElementById("visit_date").value;
  const visitTime = document.getElementById("visit_time").value;
  const message = document.getElementById("booking_message").value;

  try {
    const response = await fetch("/api/book-visit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        listing_id: listingId,
        visit_date: visitDate,
        visit_time: visitTime,
        message: message,
      }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      closeBookingModal();
      showToast("✓ " + (result.message || "Visit slot reserved successfully!"));
    } else {
      alert(result.error || "Unable to book visit. Please ensure you are logged in.");
    }
  } catch (err) {
    console.error("Booking failed:", err);
    alert("An error occurred while booking. Please try again.");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }
}

// -----------------------------------------------------------------------------
// Photo Gallery Modal Controller
// -----------------------------------------------------------------------------

function openGalleryModal(title, area, images) {
  const modal = document.getElementById("galleryModal");
  const titleEl = document.getElementById("galleryTitle");
  const subEl = document.getElementById("gallerySubtitle");
  const mainImg = document.getElementById("galleryMainImg");
  const thumbsContainer = document.getElementById("galleryThumbs");

  if (!modal || !mainImg) return;

  titleEl.textContent = title;
  subEl.textContent = `📍 ${area} • Verified Resident Photos`;

  let imgList = images;
  if (typeof images === "string") {
    try { imgList = JSON.parse(images); } catch(e) { imgList = [images]; }
  }
  if (!imgList || imgList.length === 0) {
    imgList = ["/static/images/rooms/sunrise_pg.jpg"];
  }

  mainImg.src = imgList[0];
  thumbsContainer.innerHTML = "";

  imgList.forEach((src, idx) => {
    const thumb = document.createElement("img");
    thumb.src = src;
    thumb.className = `gallery-thumb ${idx === 0 ? "active" : ""}`;
    thumb.onclick = () => {
      mainImg.src = src;
      document.querySelectorAll(".gallery-thumb").forEach(t => t.classList.remove("active"));
      thumb.classList.add("active");
    };
    thumbsContainer.appendChild(thumb);
  });

  modal.classList.remove("hidden");
}

function closeGalleryModal() {
  const modal = document.getElementById("galleryModal");
  if (modal) modal.classList.add("hidden");
}

// -----------------------------------------------------------------------------
// Online Token Advance Payment (Checkout) Controller
// -----------------------------------------------------------------------------

function openPaymentModal(listingId, name, rent) {
  const modal = document.getElementById("paymentModal");
  const idInput = document.getElementById("payListingId");
  const nameEl = document.getElementById("payListingName");
  const rentEl = document.getElementById("payListingRent");

  if (idInput) idInput.value = listingId;
  if (nameEl) nameEl.textContent = name;
  if (rentEl) rentEl.textContent = `₹${Number(rent).toLocaleString()}/month`;

  if (modal) modal.classList.remove("hidden");
}

function closePaymentModal() {
  const modal = document.getElementById("paymentModal");
  if (modal) modal.classList.add("hidden");
}

function togglePayFields(type) {
  const upiFields = document.getElementById("upiFields");
  const cardFields = document.getElementById("cardFields");

  if (type === "card") {
    upiFields.classList.add("hidden");
    cardFields.classList.remove("hidden");
  } else {
    upiFields.classList.remove("hidden");
    cardFields.classList.add("hidden");
  }
}

async function processTokenPayment(event) {
  event.preventDefault();
  const btn = document.getElementById("btnPayConfirm");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Processing Token Payment...";

  const listingId = document.getElementById("payListingId").value;
  const payMethodInput = document.querySelector('input[name="pay_method"]:checked');
  const paymentMethod = payMethodInput ? payMethodInput.value : "UPI / Google Pay";
  const paymentDetails = paymentMethod.includes("UPI") 
    ? document.getElementById("payUpiId").value 
    : document.getElementById("payCardNum").value;

  try {
    const response = await fetch("/api/token-booking", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        listing_id: listingId,
        amount: 500,
        payment_method: paymentMethod,
        payment_details: paymentDetails
      }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      closePaymentModal();
      showToast("✓ Token Payment of ₹500 Verified! Spot Reserved.");
      showReceiptModal(result);
    } else {
      alert(result.error || "Payment verification failed.");
    }
  } catch (err) {
    console.error("Payment error:", err);
    alert("Payment could not be completed. Please try again.");
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

// -----------------------------------------------------------------------------
// Digital Receipt Controller
// -----------------------------------------------------------------------------

function showReceiptModal(data) {
  const modal = document.getElementById("receiptModal");
  if (!modal) return;

  document.getElementById("recNumber").textContent = data.receipt_number || data.receipt?.receipt_number || "REC-2026";
  document.getElementById("recPaymentId").textContent = data.payment_id || data.receipt?.payment_id || "PAY-RE";
  document.getElementById("recDate").textContent = data.date || data.receipt?.created_at || new Date().toLocaleString();
  document.getElementById("recStudentName").textContent = data.student_name || data.receipt?.student_name || "Student Resident";
  document.getElementById("recListingName").textContent = data.listing_name || data.receipt?.listing_name || "Campus Residence";
  document.getElementById("recMethod").textContent = data.payment_method || data.receipt?.payment_method || "UPI";
  document.getElementById("recAmount").textContent = `₹${data.amount || data.receipt?.amount || 500}`;

  modal.classList.remove("hidden");
}

function closeReceiptModal() {
  const modal = document.getElementById("receiptModal");
  if (modal) modal.classList.add("hidden");
}

async function loadAndShowReceipt(paymentId) {
  try {
    const response = await fetch(`/api/receipt/${paymentId}`);
    const data = await response.json();
    if (response.ok && data.success) {
      showReceiptModal(data);
    } else {
      alert("Receipt not found.");
    }
  } catch (e) {
    console.error(e);
  }
}

// -----------------------------------------------------------------------------
// Direct WhatsApp Click-to-Chat Controller
// -----------------------------------------------------------------------------

async function chatWhatsApp(listingId) {
  try {
    const response = await fetch(`/api/whatsapp-link/${listingId}`);
    const data = await response.json();
    if (response.ok && data.success) {
      window.open(data.url, "_blank");
    } else {
      showToast("Unable to generate WhatsApp link.");
    }
  } catch (e) {
    console.error("WhatsApp trigger failed:", e);
  }
}

// -----------------------------------------------------------------------------
// Bookmark Controller
// -----------------------------------------------------------------------------

async function toggleBookmark(listingId, btnElement) {
  try {
    const response = await fetch("/api/save-listing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ listing_id: listingId }),
    });

    const result = await response.json();
    if (response.ok && result.success) {
      if (result.saved) {
        btnElement.classList.add("saved");
        btnElement.textContent = "★ Saved";
        showToast("✓ Room added to your saved bookmarks.");
      } else {
        btnElement.classList.remove("saved");
        btnElement.textContent = "☆ Save";
        showToast("Room removed from saved bookmarks.");
      }
    } else {
      showToast("Please sign in as a student to save rooms.");
    }
  } catch (err) {
    console.error("Save bookmark failed:", err);
  }
}

// -----------------------------------------------------------------------------
// Toast Feedback System
// -----------------------------------------------------------------------------

function showToast(message, duration = 3600) {
  const toast = document.getElementById("toastNotification");
  const msgEl = document.getElementById("toastMessage");

  if (!toast || !msgEl) return;

  msgEl.textContent = message;
  toast.classList.remove("hidden");
  toast.classList.add("visible");

  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 300);
  }, duration);
}
