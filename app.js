function toggleTheme() {

    document.body.classList.toggle("light-mode");

    const theme = document.body.classList.contains("light-mode")
        ? "light"
        : "dark";

    localStorage.setItem("studyMasterTheme", theme);

}


document.addEventListener("DOMContentLoaded", function () {

    const savedTheme = localStorage.getItem("studyMasterTheme");

    if (savedTheme === "light") {

        document.body.classList.add("light-mode");

    }

});