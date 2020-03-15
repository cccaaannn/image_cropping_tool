import os
import cv2 
import numpy as np
import argparse
import sys


def image_cropping_tool(images_path, save_folder="cropped", override_existing=False, show_cropped_images=False, max_windows_size=(1200,700), image_extensions = [".jpg", ".JPG", ".jpeg", ".png", ".PNG"]):
    """
    annotation tool for yolo labeling
    
    # warning it uses two global variables (__coords__, __drawing__) due to the opencvs mouse callback function
    # usage 
    a go backward
    d go forward
    s crop and save selected rectangle
    z delete last rectangle
    r remove all rectangles unsaved 
    """

    # read images
    images = os.listdir(images_path)
    images.sort()

    # remove not included files
    images_temp = []
    for image in images:
        image_name, image_extension = os.path.splitext(image)
        if image_extension in image_extensions: 
            images_temp.append(image) 
    images = images_temp

    # add paths to images
    images = [os.path.join(images_path, image) for image in images]

    # create save folder if not exists
    if(not os.path.exists(save_folder)):
        os.makedirs(save_folder)



    def __draw_rectangle_on_mouse_drag(event, x, y, flags, param):
        """
        draws rectangle with mouse events
        """
        global __coords__, __drawing__

        if event == cv2.EVENT_LBUTTONDOWN:
            __coords__ = [(x, y)]
            __drawing__ = True
        
        elif event == 0 and __drawing__:
            __coords__[1:] = [(x, y)]
            im = image.copy()
            cv2.rectangle(im, __coords__[0], __coords__[1], (255, 0, 0), 2)
            cv2.imshow(window_name, im) 

        elif event == cv2.EVENT_LBUTTONUP:
            # __coords__.append((x, y))
            __coords__[1:] = [(x, y)]
            __drawing__ = False


            # PREVENT POSSIBLE OUT OF IMAGE RECTANGLES 
            if(__coords__[0][0] and __coords__[1][0] > 0 and __coords__[0][0] and __coords__[1][0] < max_windows_size[0]):
                if(__coords__[0][1] and __coords__[1][1] > 0 and __coords__[0][1] and __coords__[1][1] < max_windows_size[1]):

                    cv2.rectangle(image, __coords__[0], __coords__[1], (255, 0, 0), 2)
                    # add points
                    points.append((__coords__[0],__coords__[1]))


        elif event == cv2.EVENT_RBUTTONDOWN:
            pass

    def __create_unique_file_name(file_path, before_number="(", after_number=")"):
        import os
        temp_file_path = file_path
        file_name_counter = 1
        if(os.path.isfile(temp_file_path)):
            while(True):
                save_path, temp_file_name = os.path.split(temp_file_path)
                temp_file_name, temp_file_extension = os.path.splitext(temp_file_name)
                temp_file_name = "{0}{1}{2}{3}{4}".format(temp_file_name, before_number, file_name_counter, after_number, temp_file_extension)
                temp_file_path = os.path.join(save_path, temp_file_name)
                file_name_counter += 1
                if(os.path.isfile(temp_file_path)):
                    temp_file_path = file_path
                else:
                    file_path = temp_file_path
                    break

        return file_path       



    def __find_points_on_not_resized_image(resized_shape, original_shape, points):
        # numpy is giving x and y in a wrong order (y,x,z)
        # [((x1,y1),(x2,y2)),]
        Rx = resized_shape[1]/original_shape[1]
        Ry = resized_shape[0]/original_shape[0]

        new_points = []
        for point in points:
            x1 = round(point[0][0]/Rx)
            y1 = round(point[0][1]/Ry)
            x2 = round(point[1][0]/Rx)
            y2 = round(point[1][1]/Ry)

            new_points.append(((x1,y1),(x2,y2)))

        return new_points    

    def __crop_images(original_image, points):
        resized_shape = image.shape
        original_shape = original_image.shape
        
        new_points = __find_points_on_not_resized_image(resized_shape, original_shape, points)

        croped_images = []
        for point in new_points:
            x, y, width, height = cv2.boundingRect(np.array(point))
            croped_image = original_image[y:y+height, x:x+width]
            croped_images.append(croped_image)

        return croped_images

    def __save_cropped_images(cropped_images, original_image_path, save_folder, override_existing):
        _ , file_name = os.path.split(original_image_path)
        for cropped_image in cropped_images:
            croped_image_path = os.path.join(save_folder, file_name)
            if(not override_existing):
                croped_image_path = __create_unique_file_name(croped_image_path)
            cv2.imwrite(croped_image_path, cropped_image)



    def __refresh_image(image_index, return_duplicate_of_original_image=False):
        image = cv2.imread(images[image_index])

        if(return_duplicate_of_original_image):
            duplicate_image = image.copy()

        image = cv2.resize(image, max_windows_size)

        # show some info with puttext
        cv2.putText(image, "{0}/{1}".format(len(images), image_index+1), (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color=(0, 200, 100), thickness=2)
        
        if(return_duplicate_of_original_image):
            return image, duplicate_image
        else:
            return image



    points = []
    image_index = 0
    global __drawing__
    __drawing__ = False
    window_name = "Image croping tool"


    # create window and set it up
    cv2.namedWindow(window_name)
    cv2.moveWindow(window_name, 40,30)
    cv2.setMouseCallback(window_name, __draw_rectangle_on_mouse_drag,image)
    image = __refresh_image(image_index)

    # gui loop
    while(True):

        # dont refresh the original frame while drawing
        if(not __drawing__):
            cv2.imshow(window_name, image)  
        
        key = cv2.waitKey(30)
        

        # crop and save images
        if(key == ord("s")):
            if(len(points) > 0):

                # we need duplicate of the original image we need original aspect ratio 
                image,image2 = __refresh_image(image_index,return_duplicate_of_original_image=True)
            
                cropped_images = __crop_images(image2, points)

                __save_cropped_images(cropped_images, images[image_index], save_folder, override_existing)

                if(show_cropped_images):
                    for index, croped_image in enumerate(cropped_images):
                        cv2.imshow("cropped {0}".format(index), croped_image)

                # reset points and refresh image
                # image,_ = __refresh_image(image_index)
                points = []

                print("img saved")
        
        # move backward
        if(key == ord("a")):
            if(image_index > 0):
                image_index -= 1
                image= __refresh_image(image_index)
                points = []

        # move forward
        if(key == ord("d")):
            if(image_index < len(images)-1):
                image_index += 1
                image= __refresh_image(image_index)
                points = []

        # delete last annotation
        if(key == ord("z")):
            if(points):          
                points.pop()
                image =__refresh_image(image_index)

        # refresh current image
        if(key == ord("r")):
            image =__refresh_image(image_index)
            points = []


        # if window is closed break this has to be after waitkey
        if (cv2.getWindowProperty(window_name, 0) < 0):
            # cv2.destroyAllWindows()
            break


    cv2.destroyAllWindows()


parser = argparse.ArgumentParser(description='List the content of a folder')

# Add the arguments
parser.add_argument('images_path', metavar='images_path', type=str, help='path of your images')

parser.add_argument('-f', action='store', type=str, help='save folder of the cropped images')
parser.add_argument('-o', action='store_true', help='override existing image in the folder')
parser.add_argument('-s', action='store_true', help='show cropped images')
parser.add_argument('-d', action='store', type=str, help='window dimensions w,h')
parser.add_argument('-e', action='store', type=str, help='image extensions')


# Execute the parse_args() method
args = parser.parse_args()

image_path = args.images_path


if not os.path.isdir(image_path):
    print('images path does not exist')
    sys.exit()


if(args.f):
    save_folder = args.f
else:
    save_folder="cropped"

if(args.o):
    override_existing = args.o
else:
    override_existing=False

if(args.s):
    show_cropped_images = args.s
else:
    show_cropped_images=False

if(args.d):
    try:
        dimensions = args.d.split(",")
        w = int(dimensions[0])
        h = int(dimensions[1])
        dimensions = (w,h)
        max_windows_size = dimensions
    except(ValueError):
        print('window dimensions has to be this format 1100,900')
        sys.exit()
else:
    max_windows_size=(1200,700)

if(args.e):
    try:
        extensions = args.e.split(",")
        image_extensions = extensions
    except(ValueError):
        print('window dimensions has to be this format .jpg,.png')
        sys.exit()
else:
    image_extensions = [".jpg", ".JPG", ".jpeg", ".png", ".PNG"]



image_cropping_tool(image_path, save_folder=save_folder, override_existing=override_existing, show_cropped_images=show_cropped_images, max_windows_size=max_windows_size, image_extensions=image_extensions)
