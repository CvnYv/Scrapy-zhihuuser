# -*- coding: utf-8 -*-
import scrapy
import json
from zhihuuser.items import ZhihuuserItem


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    allowed_domains = ["www.zhihu.com"]
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?incl' \
                  'ude={include}&offset={offset}&limit={limit}'
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?in' \
                    'clude={include}&offset={offset}&limit={limit}'
    start_user = 'excited-vczh'
    user_query = 'locations,employments,gender,educations,business,voteup_cou' \
                 'nt,thanked_Count,follower_count,following_count,cover_url,f' \
                 'ollowing_topic_count,following_question_count,following_fav' \
                 'lists_count,following_columns_count,avatar_hue,answer_count' \
                 ',articles_count,pins_count,question_count,commercial_questi' \
                 'on_count,favorite_count,favorited_count,logs_count,marked_a' \
                 'nswers_count,marked_answers_text,message_thread_token,accou' \
                 'nt_status,is_active,is_force_renamed,is_bind_sina,sina_weib' \
                 'o_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocke' \
                 'd,is_following,is_followed,mutual_followees_count,vote_to_c' \
                 'ount,vote_from_count,thank_to_count,thank_from_count,thanke' \
                 'd_count,description,hosted_live_count,participated_live_cou' \
                 'nt,allow_message,industry_category,org_name,org_homepage,ba' \
                 'dge[?(type=best_answerer)].topics'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_coun' \
                    't,is_followed,is_following,badge[?(type=best_answerer)].' \
                    'topics'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_co' \
                      'unt,is_followed,is_following,badge[?(type=best_answere' \
                      'r)].topics'

    def start_requests(self):
        yield scrapy.Request(
            self.user_url.format(user=self.start_user, include=self.user_query),
            self.parse_user)  # 请求第一个用户的url
        yield scrapy.Request(
            self.follows_url.format(user=self.start_user, limit=20,
                                    include=self.follows_query, offset=0),
            self.parse_follows)
        # 向服务器请求第一个用户关注的人传递给parse_follows
        yield scrapy.Request(
            self.followers_url.format(user=self.start_user, limit=20,
                                      include=self.followers_query, offset=0),
            self.parse_followers)  # 向服务器请求第一个用户的关注者传递给parse_follows

    def parse_user(self, response):  # 向服务器发送请求返回用户信息的json格式数据
        result = json.loads(response.text)
        item = ZhihuuserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item  # 获取用户信息
        yield scrapy.Request(
            self.follows_url.format(user=result.get('url_token'), limit=20,
                                    include=self.follows_query, offset=0),
            self.parse_follows)  # 向parse_follows传递该用户关注的人的请求
        yield scrapy.Request(
            self.follows_url.format(user=result.get('url_token'), limit=20,
                                    include=self.follows_query, offset=0),
            self.parse_followers)  # 向parse_followers传递该用户关注者的请求

    def parse_follows(self, response):  # 根据返回的json数据分析关注的人
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield scrapy.Request(
                    self.user_url.format(user=result.get('url_token'),
                                         include=self.user_query),
                    self.parse_user)
        # 根据data判断用户的关注的人存在,把每个单独的关注者当作用户重新请求

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield scrapy.Request(next_page, self.parse_follows)
            # 判断当前关注者列表页面是不是最后一页, 实现翻页

    def parse_followers(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield scrapy.Request(
                    self.user_url.format(user=result.get('url_token'),
                                         include=self.user_query),
                    self.parse_user)
            # 根据data判断用户的关注者存在,把每个单独的关注者当作用户重新请求

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield scrapy.Request(next_page, self.parse_followers)
            # 判断当前关注者列表页面是不是最后一页, 实现翻页