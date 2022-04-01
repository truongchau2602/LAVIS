import re
from omegaconf import OmegaConf

from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode

from common.registry import registry
from utils.randaugment import RandomAugment

from processors.base_processor import BaseProcessor


class BlipCOCOImage(BaseProcessor):
    def __init__(self, mean=None, std=None):
        if mean is None: mean = (0.48145466, 0.4578275, 0.40821073)
        if std is None: std = (0.26862954, 0.26130258, 0.27577711)

        self.normalize = transforms.Normalize(mean, std)


@registry.register_processor("blip_coco_text")
class BlipCOCOText(BaseProcessor):
    def __init__(self, prompt, max_words):
        self.prompt = prompt
        self.max_words = max_words

    def __call__(self, caption):
        caption = self.prompt + self.pre_caption(caption)
        
        return caption
    
    @classmethod
    def build_processor(cls, cfg=None):
        if cfg is None: cfg = OmegaConf.create()

        prompt = cfg.get("prompt", "")
        max_words = cfg.get("max_words", 30)

        return cls(prompt=prompt, max_words=max_words)

    def pre_caption(self, caption):
        caption = re.sub(
            r"([.!\"()*#:;~])",       
            ' ',
            caption.lower(),
        )
        caption = re.sub(
            r"\s{2,}",
            ' ',
            caption,
        )
        caption = caption.rstrip('\n') 
        caption = caption.strip(' ')

        #truncate caption
        caption_words = caption.split(' ')
        if len(caption_words) > self.max_words:
            caption = ' '.join(caption_words[:self.max_words])
                
        return caption


@registry.register_processor("blip_coco_vis_train")
class BlipCOCORetImageTrain(BlipCOCOImage):
    def __init__(self):
        super().__init__()

        self.transform = transforms.Compose([                        
                transforms.RandomResizedCrop(384, scale=(0.5, 1.0),interpolation=InterpolationMode.BICUBIC),
                transforms.RandomHorizontalFlip(),
                RandomAugment(2,5,isPIL=True,augs=['Identity','AutoContrast','Brightness','Sharpness','Equalize',
                                                'ShearX', 'ShearY', 'TranslateX', 'TranslateY', 'Rotate']),     
                transforms.ToTensor(),
                self.normalize,
            ])        
    
    def __call__(self, item):
        return self.transform(item) 


@registry.register_processor("blip_coco_vis_eval")
class BlipCOCORetImageEval(BlipCOCOImage):
    def __init__(self, image_size=384, mean=None, std=None):
        super().__init__(mean=mean, std=std)

        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size),interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            self.normalize,
            ])  

    def __call__(self, item):
        return self.transform(item) 
    
    @classmethod
    def build_processor(cls, cfg=None):
        if cfg is None: cfg = OmegaConf.create()

        image_size = cfg.get("image_size", 384)

        mean = cfg.get("mean", None)
        std = cfg.get("std", None)

        return cls(image_size=image_size, mean=mean, std=std)
