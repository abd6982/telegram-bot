import logging

from django.conf import settings
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from bot.apps import BotClient
from bot.models import Group, EngagementRule
from bot.utils import TeleClient


log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)


# https://stackoverflow.com/questions/40746137/post-save-signal-isnt-called/40883331

@receiver([post_save, post_delete], sender=Group)
def rename_image(sender, instance, created, **kwargs):
    TeleClient.setAllowedGroupIDS([])
    TeleClient.setAllowedGroups([])
    TeleClient.getAllowedGroupIDs()
    TeleClient.getAllowedGroups()


# @receiver([post_save, post_delete], sender=EngagementRule)
# def rename_image(sender, instance, created, **kwargs):
#     log.warning("****************SAVED Initializing Bot Rules *******************")
#     BotClient.get_rules(force_init=True)




# @receiver(post_save, sender=RetailerAccount, dispatch_uid="rename_uploaded_image")
# def rename_image(sender, instance, created, **kwargs):
#     try:
#         if created:
#             file_obj = instance.sLogo
#
#             conn = S3Connection(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)
#             k = Key(conn.get_bucket(settings.AWS_S3_BUCKET))
#             k.key = 'upls/%s/%s.png' % (request.user.id, upload.key)
#             k.set_contents_from_string(file_obj.read())
#
#             serializer = UploadSerializer(upload)
#
#             return Response(serializer.data, status=201)
#
#             path = instance.sLogo.path
#             print("URL:  ", instance.sLogo.url)
#             print("Path:  ", instance.sLogo.path)
#             path = path.replace(os.path.splitext(path)[0].split("/")[-1], str(instance.id))
#             copy2(instance.sLogo.path, path)
#             db_file = instance.sLogo.url.split(settings.MEDIA_URL)[1]
#             RetailerAccount.objects.filter(id=instance.id).update(sLogo=db_file.replace(db_file.split("/")[-1], "%d.%s" % (instance.id, db_file.split("/")[-1].split(".")[1])))
#             os.remove(instance.sLogo.path)
#     except (ValueError, FileNotFoundError) as e:
#         pass


# @receiver(pre_save, sender=RetailerAccount, dispatch_uid="rename_uploading_image")
# def rename_image(sender,instance, **kwargs):
#     try:
#         print("***********IN the Try*************")
#         print("URL:  ", instance.id)
#         print("URL:  ", instance.sLogo.url)
#     except (ValueError, FileNotFoundError) as e:
#         print(e)