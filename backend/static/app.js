// LOAD POSTS
    const container = document.getElementById('postsContainer');

    container.innerHTML = '';

    posts.forEach(post => {

        container.innerHTML += `

        <div class="card p-3 mb-3">
            <h4>${post.title}</h4>
            <p>${post.content}</p>
            <small>${post.created_at}</small>
        </div>

        `;
    });

// CREATE POST

const postForm = document.getElementById('postForm');

postForm.addEventListener('submit', async function(e) {

    e.preventDefault();

    const formData = new FormData();

    formData.append('title', document.getElementById('title').value);
    formData.append('content', document.getElementById('content').value);


    await fetch('/create-post', {
        method: 'POST',
        body: formData
    });


    postForm.reset();

    loadPosts();
});


// WEATHER

async function loadWeather() {

    const response = await fetch('/weather/Charlotte');

    const data = await response.json();

    document.getElementById('weather-result').innerHTML = `

        <h5>${data.city}</h5>
        <p>Temperature: ${data.temperature}°C</p>
        <p>Condition: ${data.description}</p>

    `;
}


loadPosts();