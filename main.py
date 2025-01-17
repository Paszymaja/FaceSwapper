import cv2
import numpy as np
import dlib


def extract_index_nparray(nparray):
    index = None
    for num in nparray[0]:
        index = num
        break
    return index


class Image:
    def __init__(self, image_path=None):

        if image_path is None:
            self.video_read()
        else:
            self.image_path = image_path
            self.image = self.image_read()

        self.image_gray = self.image_gray()
        self.image_mask = self.image_mask()

    def image_read(self):
        return cv2.imread(self.image_path)

    def video_read(self):
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        _, self.image = camera.read()

        self.image_gray = self.image_gray()
        self.image_mask = self.image_mask()

    def image_gray(self):
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def image_mask(self):
        return np.zeros_like(self.image_gray)

    def image_copy(self):
        return np.zeros(self.image.shape, np.uint8)


face_1 = Image('TestPhotos/Korwin.png')
face_2 = Image('TestPhotos/Maklowicz.jpg')
face_2_copy = face_2.image_copy()


class FaceSwap(Image):
    def __init__(self, image_path, detector=dlib.get_frontal_face_detector(),
                 predictor=dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')):
        super().__init__(image_path)
        self.detector = detector
        self.predictor = predictor
        self.faces = self.load_smth()

    def load_face(self):
        return self.detector(self.image_gray)

    def load_smth(self):
        faces = [face for face in self.load_face()]
        return faces

    def landmarks_points(self):
        global landmarks_points
        for face in self.faces:
            landmarks = self.predictor(self.image_gray, face)
            landmarks_points = []
            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                landmarks_points.append((x, y))
        return landmarks_points

    def smth_faces(self):
        for _ in self.load_face():
            landmarks_points = self.landmarks_points()

            points = np.array(landmarks_points, np.int32)
            convexhull = cv2.convexHull(points)
            # cv2.polylines(img, [convexhull], True, (255, 0, 0), 3)
            cv2.fillConvexPoly(self.image_mask, convexhull, 255)

            # Delaunay tringulation
            rect = cv2.boundingRect(convexhull)
            subdiv = cv2.Subdiv2D(rect)
            subdiv.insert(landmarks_points)
            triangels = subdiv.getTriangleList()
            triangels = np.array(triangels, dtype=np.int32)

            indexes_triangels = []

            for t in triangels:
                pt1 = (t[0], t[1])
                pt2 = (t[2], t[3])
                pt3 = (t[4], t[5])

                index_pt1 = np.where((points == pt1).all(axis=1))
                index_pt1 = extract_index_nparray(index_pt1)
                index_pt2 = np.where((points == pt2).all(axis=1))
                index_pt2 = extract_index_nparray(index_pt2)
                index_pt3 = np.where((points == pt3).all(axis=1))
                index_pt3 = extract_index_nparray(index_pt3)

                if index_pt1 is not None and index_pt2 is not None and index_pt3 is not None:
                    triangle = [index_pt1, index_pt2, index_pt3]
                    indexes_triangels.append(triangle)
            return indexes_triangels


a = FaceSwap('TestPhotos/Korwin.png')

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')

indexes_triangels = a.smth_faces()
landmarks_points = a.landmarks_points()

while True:
    faces2 = detector(face_2.image_gray)
    for face in faces2:
        landmarks = predictor(face_2.image_gray, face)
        landmarks_points2 = []
        for n in range(0, 68):
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            landmarks_points2.append((x, y))

            points2 = np.array(landmarks_points2, np.int32)
            convexhull2 = cv2.convexHull(points2)

    lines_space_mask = np.zeros_like(face_1.image_gray)
    lines_space_new_face = np.zeros_like(face_2.image)

    # Triangulation of faces
    for triangle_index in indexes_triangels:
        # Triangulation of the first face
        tr1_pt1 = landmarks_points[triangle_index[0]]
        tr1_pt2 = landmarks_points[triangle_index[1]]
        tr1_pt3 = landmarks_points[triangle_index[2]]
        triangle1 = np.array([tr1_pt1, tr1_pt2, tr1_pt3], np.int32)

        rect1 = cv2.boundingRect(triangle1)
        (x, y, w, h) = rect1
        cropped_tr1 = face_1.image[y: y + h, x: x + w]
        cropped_tr1_mask = np.zeros((h, w), np.uint8)

        points = np.array([[tr1_pt1[0] - x, tr1_pt1[1] - y],
                           [tr1_pt2[0] - x, tr1_pt2[1] - y],
                           [tr1_pt3[0] - x, tr1_pt3[1] - y]], np.int32)

        cv2.fillConvexPoly(cropped_tr1_mask, points, 255)

        work_mode = 0
        if work_mode == 0:
            cv2.line(lines_space_mask, tr1_pt1, tr1_pt2, 255)
            cv2.line(lines_space_mask, tr1_pt2, tr1_pt3, 255)
            cv2.line(lines_space_mask, tr1_pt1, tr1_pt3, 255)
            lines_space = cv2.bitwise_and(face_1.image, face_1.image, mask=lines_space_mask)

        # Triangulation of the second face
        tr2_pt1 = landmarks_points2[triangle_index[0]]
        tr2_pt2 = landmarks_points2[triangle_index[1]]
        tr2_pt3 = landmarks_points2[triangle_index[2]]
        triangle2 = np.array([tr2_pt1, tr2_pt2, tr2_pt3], np.int32)

        rect2 = cv2.boundingRect(triangle2)
        (x, y, w, h) = rect2
        cropped_tr2_mask = np.zeros((h, w), np.uint8)

        points2 = np.array([[tr2_pt1[0] - x, tr2_pt1[1] - y],
                            [tr2_pt2[0] - x, tr2_pt2[1] - y],
                            [tr2_pt3[0] - x, tr2_pt3[1] - y]], np.int32)

        cv2.fillConvexPoly(cropped_tr2_mask, points2, 255)

        # Wrap triangles
        points = np.float32(points)
        points2 = np.float32(points2)
        M = cv2.getAffineTransform(points, points2)
        warped_triangle = cv2.warpAffine(cropped_tr1, M, (w, h))
        warped_triangle = cv2.bitwise_and(warped_triangle, warped_triangle, mask=cropped_tr2_mask)

        # Reconstruct new face without white lines
        img2_new_face_rect_area = face_2_copy[y: y + h, x: x + w]
        img2_new_face_rect_area_gray = cv2.cvtColor(img2_new_face_rect_area, cv2.COLOR_BGR2GRAY)
        _, mask_triangles_designed = cv2.threshold(img2_new_face_rect_area_gray, 1, 255, cv2.THRESH_BINARY_INV)
        warped_triangle = cv2.bitwise_and(warped_triangle, warped_triangle, mask=mask_triangles_designed)

        img2_new_face_rect_area = cv2.add(img2_new_face_rect_area, warped_triangle)
        face_2_copy[y: y + h, x: x + w] = img2_new_face_rect_area

    # Put on new face
    img2_face_mask = np.zeros_like(face_2.image_gray)
    img2_head_mask = cv2.fillConvexPoly(img2_face_mask, convexhull2, 255)
    img2_face_mask = cv2.bitwise_not(img2_head_mask)

    img2_head_noface = cv2.bitwise_and(face_2.image, face_2.image, mask=img2_face_mask)
    result = cv2.add(img2_head_noface, face_2_copy)

    # Smoothing transition of images
    (x, y, w, h) = cv2.boundingRect(convexhull2)
    center_face2 = (int((x + x + w) / 2), int((y + y + h) / 2))

    final_face = cv2.seamlessClone(result, face_2.image, img2_head_mask, center_face2, cv2.NORMAL_CLONE)

    if work_mode == 1:
        cv2.imshow("result", result)
    else:
        cv2.imshow("Final face", final_face)

    key = cv2.waitKey(33)
    if key == 27:
        break
cv2.destroyAllWindows()
