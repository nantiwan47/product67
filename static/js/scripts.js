document.addEventListener("DOMContentLoaded", function () {
    const userDropdown = document.getElementById("userDropdown");
    const dropdownMenu = document.getElementById("dropdownMenu");

    if (userDropdown && dropdownMenu) {
        userDropdown.addEventListener("click", function (event) {
            event.stopPropagation(); // ป้องกัน dropdown ปิดเมื่อคลิกที่ตัวเอง
            dropdownMenu.classList.toggle("show");
        });

        // ปิด dropdown เมื่อคลิกที่อื่น
        document.addEventListener("click", function (event) {
            if (!userDropdown.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.remove("show");
            }
        });
    }
});