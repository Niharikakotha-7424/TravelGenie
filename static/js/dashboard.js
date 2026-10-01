document.addEventListener(
    "DOMContentLoaded",
    function () {

        const deleteForms =
            document.querySelectorAll(
                "form[action*='delete-trip']"
            );

        deleteForms.forEach(
            function (form) {

                form.addEventListener(
                    "submit",
                    function (event) {

                        const confirmed =
                            confirm(
                                "Delete this saved trip?"
                            );

                        if (!confirmed) {
                            event.preventDefault();
                        }

                    }
                );

            }
        );

    }
);