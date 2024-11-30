
    const btn = document.querySelector('#fetchDrug');
    btn.addEventListener('click', (e) => {
        const inp = document.querySelector('#drugName');
        const drugsObj = [{
            name: inp.value,
        }]
        fetchData(drugsObj)
        .then((response) => {
            console.log(response);
            const generalPrecautionsElem = document.querySelector('#generalPrecautions');
            // const precautionsTableElem = document.querySelector('#precautionsTable');
            const generalPrecautionsTableElem = document.querySelector('#generalPrecautionsTable');

            if (response.general_precautions && response.general_precautions.length > 0) {
                generalPrecautionsElem.innerHTML = response.general_precautions.join('<br><br>');
            } else {
                generalPrecautionsElem.textContent = 'No general precautions available.';
            }

            if (response.precautions_table && response.precautions_table.length > 0) {
                // precautionsTableElem.innerHTML = response.precautions_table[0]; // Render the HTML table directly
            } else {
                // precautionsTableElem.textContent = 'No precautions table available.';
            }

     
            if (response.general_precautions_table && response.general_precautions_table.length > 0) {
                generalPrecautionsTableElem.innerHTML = response.general_precautions_table[0]; // Render the HTML table directly
            } else {
                generalPrecautionsTableElem.textContent = 'No general precautions table available.';
            }
        })
        .catch((error) => {
            console.error("Error fetching data:", error);
            const cont = document.querySelector('#responseMessage');
            cont.textContent = 'Error fetching data: ' + error.message;
        });
    });

    async function fetchData(drugsObj) {
        for (const obj of drugsObj) {   
            const drugName = obj.name;
            const url = "https://api.fda.gov/drug/label.json?search=";
            let limit = 1;
            try {
                const response = await fetch(`${url}${drugName}&limit=${limit}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json(); // Parse the JSON from the response
                return data.results[0]; // Return the first result
            } catch (error) {
                console.error('Fetch error: ', error);
                throw error;  // Propagate the error to the caller
            }
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('imageUploadForm');
    const imageInput = document.getElementById('imageInput');
    const responseMessage = document.getElementById('responseMessage');

    form.addEventListener('submit', async function(event) {
        event.preventDefault();  

        // Check if an image is selected
        if (!imageInput.files.length) {
            responseMessage.innerText = 'Please select an image.';
            return;
        }

        // Create FormData and append the image
        const formData = new FormData();
        formData.append('image', imageInput.files[0]);

        try {
            // Send the POST request to the Flask endpoint
            const response = await fetch('/upload_image_to_flask/', {
                method: 'POST',
                body: formData,
            });

            // Check if response is OK and handle JSON response
            if (response.ok) {
                const data = await response.json(); // Parse the JSON response
                console.log('JSON Response:', data); // Debugging: log the full response

                // Send the parsed JSON to the Django endpoint
                const djangoResponse = await fetch('/process_medicines/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: data.text }),
                });

                if (djangoResponse.ok) {
                    const djangoData = await djangoResponse.json();
                    responseMessage.innerText = 'Medicines: ' + djangoData.medicines.join(', ');
                } else {
                    const djangoError = await djangoResponse.json();
                    responseMessage.innerText = 'Error processing medicines: ' + djangoError.error;
                }
            } else {
                // Handle non-200 responses
                const data = await response.json();
                responseMessage.innerText = 'Error: ' + (data.error || 'An error occurred');
                console.error('Response Error:', data);
            }
        } catch (error) {
            // Handle network or other errors
            responseMessage.innerText = 'Error uploading image: ' + error.message;
            console.error('Fetch Error:', error);
        }
    });
});
