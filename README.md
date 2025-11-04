# Veo Ad Generator Demo

This repository contains a lightweight prototype for turning product 3D models into
advertising videos by calling Google Veo 2/3. The implementation is dependency-free and
runs on top of the Python standard library so it works in restricted environments.

> **Important:** the Google Veo integration is mocked. Replace the placeholder code in
> `generate_video_using_veo` with a real API request once you have credentials.

## Features

- Upload `.gltf` or `.glb` product models from the browser
- Optional advertising prompt that influences the generated video
- Server-side validation and temporary storage for uploads
- Mock Veo client that illustrates the response shape expected by the UI
- Single-page front-end that displays job metadata and plays the resulting video URL

## Getting started

1. Make sure Python 3.9+ is installed.
2. Start the server:

   ```bash
   python src/server.py
   ```

3. Open the app at [http://localhost:8000](http://localhost:8000).
4. Upload a sample GLTF/GLB file and (optionally) enter an advertising prompt.

The mocked integration will always return the same demo video URL along with metadata.

## Integrating with Google Veo

To hook the prototype up to the real Veo 2/3 service:

1. Obtain API credentials from Google and store them as environment variables or secrets.
2. Replace the implementation of `generate_video_using_veo` in `src/server.py` with an HTTP
   client that calls the Veo REST endpoint. A typical request would:
   - Include the 3D asset in the multipart/form-data body
   - Pass your creative brief or prompt as JSON metadata
   - Authenticate using the API key or OAuth token supplied by Google
3. Update the front-end to poll the job status if Veo processes videos asynchronously.
4. Surface the final video URL or download link returned by Veo in `public/app.js`.

Because the server uses only the Python standard library you are free to swap in your
preferred HTTP client or migrate the code to a more feature-rich framework if desired.
