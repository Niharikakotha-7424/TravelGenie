document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById("plannerForm");

        if (!form) {
            return;
        }

        form.addEventListener(
            "submit",
            function () {

                const button =
                    form.querySelector(
                        ".generate-btn"
                    );

                if (button) {

                    button.innerHTML =
                        "🤖 Creating your smart trip...";

                    button.disabled = true;
                }

            }
        );

    }
);