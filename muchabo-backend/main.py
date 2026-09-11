

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("muchabo.app:app", host="0.0.0.0", port=8080, reload=False)
