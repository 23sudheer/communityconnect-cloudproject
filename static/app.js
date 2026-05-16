async function loadPosts() {

    const response = await fetch('/posts');

    const posts = await response.json();

    const container = document.getElementById('postsContainer');

    container.innerHTML = '';

    posts.forEach(post => {

        container.innerHTML += `

        <div class="card p-3 mb-3">

            <h3>${post.title}</h3>

            <p>${post.content}</p>

            ${
                post.image_url
                ? `<img src="${post.image_url}" class="mb-3">`
                : ''
            }

            <button
                class="btn btn-danger"
                onclick="deletePost(${post.id})"
            >
                Delete
            </button>

        </div>

        `;
    });
}

document.getElementById('postForm').addEventListener('submit', async function(e) {

    e.preventDefault();

    const formData = new FormData();

    formData.append('title', document.getElementById('title').value);

    formData.append('content', document.getElementById('content').value);

    formData.append('image', document.getElementById('image').files[0]);

    await fetch('/create-post', {
        method: 'POST',
        body: formData
    });

    this.reset();

    loadPosts();
});

async function deletePost(postId) {

    await fetch(`/delete-post/${postId}`, {
        method: 'DELETE'
    });

    loadPosts();
}

async function loadWeather() {

    const response = await fetch('/weather/Charlotte');

    const data = await response.json();

    document.getElementById('weather-result').innerHTML = `

        <h4>${data.city}</h4>

        <p>Temperature: ${data.temperature}°C</p>

        <p>Condition: ${data.description}</p>

        <p>Humidity: ${data.humidity}%</p>

    `;
}

loadPosts();