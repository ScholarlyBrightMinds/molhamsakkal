document.addEventListener('DOMContentLoaded', function () {
    // Hamburger Menu Toggle for Mobile
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const hasSubmenu = document.querySelectorAll('.nav-dropdown');

    // Toggle main menu visibility
    function toggleMenu() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('show');
    }

    // Close the menu
    function closeMenu() {
        hamburger.classList.remove('active');
        navMenu.classList.remove('show');
    }

    // Hamburger click event for mobile
    hamburger.addEventListener('click', function (event) {
        event.stopPropagation();
        toggleMenu();
    });

    // Close the menu if clicking outside of it
    document.addEventListener('click', function (event) {
        if (!navMenu.contains(event.target) && !hamburger.contains(event.target) && hamburger.classList.contains('active')) {
            closeMenu();
        }
    });

    // Toggle submenu open/close behavior for mobile
    hasSubmenu.forEach(item => {
        const submenuToggle = item.querySelector('.nav-item');
        const submenu = item.querySelector('.dropdown-content');
        const arrow = submenuToggle.querySelector('.arrow'); // Get the arrow element

        submenuToggle.addEventListener('click', function (event) {
            if (window.innerWidth <= 768) {
                event.preventDefault();
                item.classList.toggle('active');
                submenu.style.display = item.classList.contains('active') ? 'block' : 'none';

                // Rotate the arrow
                if (arrow) {
                    arrow.style.transform = item.classList.contains('active') ? 'rotate(-45deg)' : 'rotate(135deg)';
                }
            }
        });
    });

    // Handle window resizing (reset styles if switching to desktop view)
    function handleWindowChanges() {
        if (window.innerWidth > 768) {
            hasSubmenu.forEach(item => {
                item.classList.remove('active');
                const submenu = item.querySelector('.dropdown-content');
                const arrow = item.querySelector('.arrow');
                if (submenu) submenu.style.display = '';
                if (arrow) arrow.style.transform = 'rotate(135deg)';
            });
            navMenu.classList.remove('show');
            hamburger.classList.remove('active');
        }
    }

    window.addEventListener('resize', handleWindowChanges);

    // Read More functionality for project descriptions on mobile
    const readMoreLinks = document.querySelectorAll('.read-more');

    // Function to handle read more behavior
    function handleReadMoreVisibility() {
        readMoreLinks.forEach((link) => {
            const projectDescription = link.closest('.project-description');
            const shortDescription = projectDescription.querySelector('.short-description');
            const fullDescription = projectDescription.querySelector('.full-description');

            if (window.innerWidth <= 768) {
                // Show only short description and hide the full description on mobile screens
                shortDescription.style.display = 'block';
                fullDescription.style.display = 'none';
                link.style.display = 'inline-block';
                link.textContent = 'Read more';
            } else {
                // Show only the full description on desktop screens, hide short description and Read More link
                shortDescription.style.display = 'none';
                fullDescription.style.display = 'block';
                link.style.display = 'none';
            }
        });
    }

    // Initial check when the page loads
    handleReadMoreVisibility();

    // Listen for window resize events to adjust read more visibility
    window.addEventListener('resize', handleReadMoreVisibility);

    // Add event listeners to the read more links
    readMoreLinks.forEach((link) => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const projectDescription = this.closest('.project-description');
            const shortDescription = projectDescription.querySelector('.short-description');
            const fullDescription = projectDescription.querySelector('.full-description');

            // Toggle visibility of the descriptions
            if (fullDescription.style.display === 'none' || !fullDescription.style.display) {
                fullDescription.style.display = 'block'; // Show the full description
                shortDescription.style.display = 'none'; // Hide the short description
                this.textContent = 'Read less'; // Change the link text
            } else {
                fullDescription.style.display = 'none'; // Hide the full description
                shortDescription.style.display = 'block'; // Show the short description
                this.textContent = 'Read more'; // Change the link text
            }
        });
    });
});
