document.addEventListener('DOMContentLoaded', (e) => {
    $('#myForm').on('submit', function(e) {
        e.preventDefault();
        var formData = $(this).serializeArray();
        var jsonData = {};

        $.each(formData, function() {
            if (jsonData[this.name]) {
                if (!jsonData[this.name].push) {
                    jsonData[this.name] = [jsonData[this.name]];
                }
                jsonData[this.name].push(this.value || '');
            } else {
                jsonData[this.name] = this.value || '';
            }
        });

        console.log(jsonData); // Here's your JSON data
    });
});