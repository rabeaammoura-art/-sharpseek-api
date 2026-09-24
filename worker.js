export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({
        ok: true,
        app: "SharpSeek",
        message: "API is running"
      });
    }

    if (url.pathname === "/search") {
      const query = url.searchParams.get("q");

      if (!query) {
        return Response.json(
          { error: "Missing search query. Use ?q=product" },
          { status: 400 }
        );
      }

      return Response.json({
        ok: true,
        query,
        offers: []
      });
    }

    return Response.json({
      app: "SharpSeek",
      status: "online"
    });
  }
};
