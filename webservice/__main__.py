import os
import aiohttp
import requests
import pdb
import json 

from aiohttp import web

#from gidgethub import routing, sansio
#from gidgethub import aiohttp as gh_aiohttp

routes = web.RouteTableDef()

base_bitbucket_url = os.environ['BITBUCKETURL']
bitbucket_api_token = os.environ['BITBUCKETAPITOKEN']
base_bitbucket_api_url = f'{base_bitbucket_url}/rest/api/1.0'
#base_bitbucket_api_url = f'{base_bitbucket_url}'
bitbucket_headers = {"Authorization": f"Bearer {bitbucket_api_token}", "X-Atlassian-Token": "no-check"}

#router = routing.Router()

#@router.register("issues", action="opened")
#async def issue_opened_event(event, gh, *args, **kwargs):
#    """ Whenever an issue is opened, greet the author and say thanks."""
#
#    url = event.data["issue"]["comments_url"]
#    author = event.data["issue"]["user"]["login"]
#
#    message = f"Thanks for the report @{author}! I will look into it ASAP! (I'm a bot)."
#    print(f"message: @{message}")
#    #await gh.post(url, data={"body": message})

#@router.register("pull_request", action="opened")
#async def pull_request_opened_event(event, gh, *args, **kwargs):
#    """    Whenever an pull request is opened, lets see what to do    """
#    print("Testing 1")
#    url = event.data["pull_request"]
#    print(f"Event: @{url}")
#    #await gh.post(url, data={"body": message})

#@router.register("pull_request_review_comment", action="created")
#async def pul_request_review_comment_created_event(event, gh, *args, **kwargs):
#    """   Whereever there is a PR comment, lets see what to do   """
#   print(f"Event: @{event}")
#    comment = event.data["comment"]
#    print(f"Comment: @{comment}")

@routes.post("/")
async def main(request):
    data = await request.json()
    #data = await json.loads(request.text)
    print(f'Event = {json.dumps(data)}')
    bot_slug = requests.get(url=f'{base_bitbucket_url}/plugins/servlet/applinks/whoami', headers=bitbucket_headers).text
    #bot_slug = requests.get(url=f'{base_bitbucket_url}/plugins/servlet/applinks/whoami').text
    print(f'URL:{base_bitbucket_url}/plugins/servlet/applinks/whoami')
    print(f'headers:{bitbucket_headers}')
    #bot_slug = data.get('actor', {}).get('name')
    project = data.get('pullRequest', {}).get('toRef').get('repository').get('project').get('key')
    repo = data.get('pullRequest', {}).get('toRef').get('repository').get('name')
    pr_id = data.get('pullRequest', {}).get('id')
    pr_version = data.get('pullRequest', {}).get('version')
    author_name = data.get("pullRequest", {}).get("author").get("user").get("name")
    author_display_name = data.get("pullRequest", {}).get("author").get("user").get("displayName")
    actor_display_name = data.get('actor', {}).get('displayName')
    src_ref_id = data.get('pullRequest', {}).get('fromRef').get('id')
    src_repo_id = data.get('pullRequest', {}).get('fromRef').get('repository').get('id')
    target_ref_id = data.get('pullRequest', {}).get('toRef').get('id')
    target_repo_id = data.get('pullRequest', {}).get('toRef').get('repository').get('id')
    target_branch = data.get('pullRequest', {}).get('toRef').get('displayId')
    base_pr_url = f'{base_bitbucket_api_url}/projects/{project}/repos/{repo}/pull-requests/{pr_id}'
    source_branch = data.get('pullRequest', {}).get('fromRef').get('displayId').split('/')[0]
        
    def is_pr_mergable(base_pr_url, headers):
        pdb.set_trace()
        merge_status_url = f'{base_pr_url}/merge'
        merge_status = requests.get(merge_status_url, headers=headers).json()

        if merge_status.get('canMerge') is True and not merge_status.get('conflicted') and \
                merge_status.get('outcome') == 'CLEAN':
            app.logger.debug('PR is mergable, returning True')
            return True
        else:
            return False

    def approve_pr(base_pr_url, headers, slug):
        pdb.set_trace()
        approval_url = f'{base_pr_url}/participants/{slug}'
        json_body = {'status': 'APPROVED'}
        r = requests.put(url=approval_url, headers=headers, json=json_body)

        return r

    def merge_pr(base_pr_url, pr_version, headers):
        pdb.set_trace()
        merge_url = f'{base_pr_url}/merge?version={pr_version}'
        r = requests.post(url=merge_url, headers=headers)
        return r

    if source_branch == 'release' and target_branch == 'master':
        if data.get('eventKey', {}) == 'pr:comment:added':

            comment_text = data.get('comment', {}).get('text')
            print(f"comment_text = {comment_text}")
            pdb.set_trace()
            if comment_text.casefold() == '/approve merge UAT deploy'.casefold():
                r = approve_pr(base_pr_url=base_pr_url, headers=bitbucket_headers, slug=bot_slug)
                is_mergable = is_pr_mergable(base_pr_url=base_pr_url, headers=bitbucket_headers)
                if is_mergable:
                    merge_pr(base_pr_url=base_pr_url, pr_version=pr_version, headers=bitbucket_headers)
    else:
        print(f'Silently ignoring the event as the merge is not between release->master')
                
   
    return web.Response(status=200)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
