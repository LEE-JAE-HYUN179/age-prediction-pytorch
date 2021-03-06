import torch
import cv2
import numpy as np
import torchvision.transforms as transforms
import torch.nn.functional as F
from detector import face_detector
import model.DenseNet as Densenet

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
age_tensor = torch.tensor([i for i in range(1, 101)]).type(torch.FloatTensor).to(device)


def image_loader(image):
    transform_img = transforms.Compose(
        [transforms.ToPILImage(),
         transforms.Resize(224),
         transforms.ToTensor(),
         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 의미?
         ]
    )
    """load image, returns cuda tensor"""
    image = np.array(image)
    image = transform_img(image).float()
    image = image.unsqueeze(0)
    return image.to(device)  # assumes that you're using CPU


def predict(img, model):
    faces, img_list = face_detector(img)
    if not img_list:
        return img

    out_list = []
    for face_img in img_list:
        output = model(image_loader(face_img))
        output = F.softmax(output, dim=1)
        output = (output * age_tensor).sum(dim=1)
        out_list.append(output)

    for (x, y, w, h), age in zip(faces, out_list):
        img = cv2.rectangle(img, pt1=(x, y), pt2=(x + int(w), y + int(h)),
                            color=(255, 0, 0))
        cv2.putText(img, text='Age: {:.3f}'.format(age.item(), 3), org=(max(0, x - int(w / 4)), max(0, y - int(4 / h))),
                    fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    fontScale=0.7,
                    color=(255, 255, 0))

    return img


def real_time():
    dense121_path = './trained_model/densenet121.pt'
    dense121_model = Densenet.get_densenet121()
    dense121_model.load_state_dict(torch.load(dense121_path))
    dense121_model.to(device)
    dense121_model.eval()

    cap = cv2.VideoCapture(0)

    if cap.isOpened():
        print('succecfully streaming')
    while True:
        ret, frame = cap.read()

        if ret:
            if cv2.waitKey(3) & 0XFF == ord('q'):
                break
            cv2.imshow('webcam', predict(frame, dense121_model))

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    real_time()
