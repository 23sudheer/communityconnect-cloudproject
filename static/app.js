async function loadPosts() {

    const response = await fetch('/posts');

    const posts = await response.json();

    const container = document.getElementById('postsContainer');

    container.innerHTML = '';

    posts.forEach(post => {

        const commentsHtml = post.comments.map(c => `
            <div class="border-top pt-2 mt-2">
                <strong>${c.author}</strong>
                <span class="text-muted small">${c.created_at}</span>
                <div>${c.comment}</div>
            </div>
        `).join('');

        container.innerHTML += `

        <div class="card p-3 mb-3">

            <h3>${post.title}</h3>
            <p class="text-muted small mb-2">by ${post.author} · ${post.created_at}</p>
            <p>${post.content}</p>

            ${
                post.image_url
                ? `<img src="${post.image_url}" class="mb-3">`
                : ''
            }

            <button
                class="btn btn-danger btn-sm"
                onclick="deletePost(${post.id})"
            >
                Delete
            </button>

            <div class="mt-3">
                <h6>Comments</h6>
                <div id="comments-${post.id}">${commentsHtml}</div>

                <div class="input-group mt-2">
                    <input
                        type="text"
                        class="form-control"
                        id="comment-input-${post.id}"
                        placeholder="Add a comment..."
                    >
                    <button
                        class="btn btn-outline-primary"
                        onclick="addComment(${post.id})"
                    >
                        Post
                    </button>
                </div>
            </div>

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

async function addComment(postId) {

    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();

    if (!text) return;

    const formData = new FormData();
    formData.append('post_id', postId);
    formData.append('comment', text);

    await fetch('/add-comment', {
        method: 'POST',
        body: formData
    });

    input.value = '';

    loadPosts();
}

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
