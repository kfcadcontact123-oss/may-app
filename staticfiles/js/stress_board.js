// ===== VN TIME =====
const now = new Date();

const vnTime = new Date(
  now.toLocaleString("en-US", {
    timeZone: "Asia/Ho_Chi_Minh"
  })
);

const weekdays = [
  "Chủ nhật",
  "Thứ hai",
  "Thứ ba",
  "Thứ tư",
  "Thứ năm",
  "Thứ sáu",
  "Thứ bảy"
];

// ===== SAFE RENDER =====
const dayEl = document.getElementById("today-day");
if (dayEl) {
  dayEl.textContent = weekdays[vnTime.getDay()];
}

const dateEl = document.getElementById("today-date");
if (dateEl) {
  dateEl.textContent = vnTime.toLocaleDateString("vi-VN");
}


// ===== DAY STREAK =====
const START_KEY = "stress_start_date";

if (!localStorage.getItem(START_KEY)) {
  localStorage.setItem(START_KEY, vnTime.toISOString());
}

const startDate = new Date(localStorage.getItem(START_KEY));

const diffDays =
  Math.floor((vnTime - startDate) / (1000*60*60*24)) + 1;

const numEl = document.getElementById("day-number");
if (numEl) {
  numEl.textContent = diffDays;
}