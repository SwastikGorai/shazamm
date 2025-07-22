const recordButton = document.getElementById('recordButton');
const recordIcon = document.getElementById('record-icon');
const stopIcon = document.getElementById('stop-icon');
const resultDiv = document.getElementById('result');
const confidenceDiv = document.getElementById('confidence');

let mediaRecorder;
let audioChunks = [];

recordButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordIcon.style.display = 'block';
        stopIcon.style.display = 'none';
        recordButton.classList.remove('recording');
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                recordIcon.style.display = 'none';
                stopIcon.style.display = 'block';
                recordButton.classList.add('recording');
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.wav');

                    fetch('/api/recognize', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.song) {
                            resultDiv.textContent = `Song identified: ${data.song.title} by ${data.song.artist}`;
                            confidenceDiv.textContent = `Confidence: ${data.song.confidence}`;
                        } else {
                            resultDiv.textContent = 'Song not recognized.';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        resultDiv.textContent = 'An error occurred.';
                    });
                });
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                resultDiv.textContent = 'Could not access microphone.';
            });
    }
});
