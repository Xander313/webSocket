async function refreshToken() {

    const refresh = localStorage.getItem("refresh");

    if (!refresh) {
        logout();
        return;
    }

    const res = await fetch("/api/refresh/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            refresh: refresh
        })
    });

    if (res.ok) {
        const data = await res.json();

        localStorage.setItem("token", data.access);
        document.cookie = `access=${data.access}; path=/`;
    } else {
        logout();
    }
}


async function authFetch(url, options = {}) {

    let token = localStorage.getItem("token");

    if (!token) {
        window.location = "/";
        return;
    }

    options.headers = {
        ...options.headers,
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    };

    let res = await fetch(url, options);

    // Token expirado
    if (res.status === 401) {
        await refreshToken();

        token = localStorage.getItem("token");
        options.headers.Authorization = "Bearer " + token;

        res = await fetch(url, options);
    }

    return res;
}

async function logout() {

    console.log("LOGOUT EJECUTADO");

    const refresh = localStorage.getItem("refresh");

    if (refresh) {
        await fetch("/api/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                refresh: refresh
            })
        });
    }

    localStorage.clear();
    document.cookie = "access=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";

    window.location.replace("/");
}
