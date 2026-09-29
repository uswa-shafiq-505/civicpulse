import http from 'k6/http';

export const options = {
  vus: 200,
  duration: '4m',
};

export default function () {
  const payload = JSON.stringify({
    text: `Load test complaint ${Math.random()} please ignore this request.`,
    location: 'Test Street 1',
  });
  http.post('http://localhost:8000/api/complaints', payload, {
    headers: { 'Content-Type': 'application/json' },
  });
}