# cv2.VideoCapture()

## cv2.VideoCapture()이 무엇인가?
`cv.VideoCapture`는 OpenCV에서 영상 파일이나 카메라를 열어서 프레임을 하나씩 읽어오는 객체이다.

```python
import cv2

cap = cv2.VideoCapture("video.mp4")
```

이제 python으로 해당 비디오의 프레임을 한 장씩 가져올 수 있다.

**기본적으로 다음과 같이 사용할 수 있다.**

```python
import cv2

cap = cv2.VideoCapture("video.mp4")

if not cap.isOpened():
    raise FileNotFoundError("비디오를 열 수 없다.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
```

### `cap.isOpened()`란?
비디오가 제대로 열렸는지 확인한다.
파일 경로가 틀렸거나, 파일이 깨졌거나, [*코덱 문제가 있으면 열리지 않을 수 있다.

## 번외, 코덱이 무엇인가?

