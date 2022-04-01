import os
from instaloader import Profile, Post

class IgpdLinuxFeaturesPrivate:

    def download_post(self,link,p_instance_param):
        pid = link.rsplit("/",2)[-2]

        post = Post.from_shortcode(p_instance_param.context, pid)
        p_instance_param.download_post(post,target=(pid))

        print("\nPost downloaded successful and saved in -- "+ pid)

    def download_story(self,s_username,s_instance_param):

        profile = Profile.from_username(s_instance_param.context, username=s_username)

        s_instance_param.download_stories(userids=[profile.userid],filename_target='{}/stories'.format(profile.username))

        print("Story downloaded successfully and saved as {}/stories".format(profile.username))

    def download_highlights(self,h_username,h_instance_param):
        profile = Profile.from_username(h_instance_param.context, username= h_username)

        for highlight in h_instance_param.get_highlights(user=profile):
            # highlight is a Highlight object
            for item in highlight.get_items():
                # item is a StoryItem object
                h_instance_param.download_storyitem(item, '{}/{}'.format(highlight.owner_username, highlight.title))

        print("\nHighlights downloaded successful and saved as {}/{}".format(highlight.owner_username, highlight.title))
    
    def download_profile(self,pf_username,pf_instance_param):

        pf_instance_param.download_profile(profile_name=pf_username)

        print("\nProfile download successful and saved as -- "+ pf_username)


class IgpdLinuxFeaturesPublic:

    def download_pri(self,link):
        pid = link.rsplit("/",2)[-2]

        os.system(f"instaloader -- -{pid}")
    
    def download_profile(self,username):
        os.system(f"instaloader {username}")




