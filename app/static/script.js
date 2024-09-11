// Initialize slide index
let slideIndex = 0;

// Function to show slides
function showSlides() {
    const slides = document.getElementsByClassName("mySlides");
    
    // Hide all slides
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";  
    }
    
    // Increment slide index
    slideIndex++;
    
    // Reset to first slide if at the end
    if (slideIndex > slides.length) {
        slideIndex = 1;
    }
    
    // Display the current slide
    if (slides[slideIndex - 1]) {
        slides[slideIndex - 1].style.display = "block";  
    }
    
    // Change image every 2 seconds
    setTimeout(showSlides, 2000); 
}

// Initialize slideshow when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    showSlides(); // Start the slideshow
});

// Fetch suggestions from API and set up autocomplete
$(document).ready(function() {
    function fetchSuggestions(query) {
        return $.ajax({
            url: '/api/suggestions',
            method: 'GET',
            data: { query: query },
            dataType: 'json'
        });
    }

    function displaySuggestions(suggestions) {
        const suggestionBox = $('#suggestion-box');
        suggestionBox.empty(); // Clear previous suggestions
    
        if (suggestions.length > 0) {
            suggestionBox.show(); // Show suggestion box if there are suggestions
    
            suggestions.forEach(function(suggestion) {
                const suggestionItem = $('<div>').text(suggestion.name).addClass('suggestion-item');
                suggestionItem.on('click', function() {
                    $('#search-input').val(suggestion.name);
                    console.log('Selected suggestion:', suggestion.name); // Debugging
                    suggestionBox.hide(); // Hide suggestions after selection
                    $('#search-form').submit(); // Submit the form after selection
                });
                suggestionBox.append(suggestionItem);
            });
        } else {
            suggestionBox.hide(); // Hide if no suggestions
        }
    }
    

    $('#search-input').on('input', function() {
        const query = $(this).val();
        if (query.length > 1) { // Only fetch suggestions if the query length is greater than 1
            fetchSuggestions(query)
                .done(data => {
                    console.log('Suggestions received:', data); // Debugging
                    displaySuggestions(data);
                })
                .fail(() => {
                    console.log('Error fetching suggestions'); // Debugging
                    $('#suggestion-box').hide(); // Hide if the request fails
                });
        } else {
            $('#suggestion-box').hide(); // Hide suggestion box if query is too short
        }
    });

    // Hide suggestion box when clicking outside of it
    $(document).on('click', event => {
        if (!$(event.target).closest('#search-input').length && !$(event.target).closest('#suggestion-box').length) {
            $('#suggestion-box').hide();
        }
    });
});








