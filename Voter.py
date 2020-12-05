import re
from collections import defaultdict
import discord
import setting

REACTION1 = setting.REACTION1
REACTION2 = setting.REACTION2
REACTION3 = setting.REACTION3
POSITIVE = setting.REACTION1_TEXT
NEGATIVE = setting.REACTION2_TEXT
STOP = setting.REACTION3_TEXT
TITLE = setting.TITLE
IDX_P = 0
IDX_N = 1
INITIAL = "---"


class Voter(object):

    def __init__(self):
        # コンストラクタ

        self.vote_dict = defaultdict(dict)

    def init(self, client):
        # bot起動時に呼び出される

        self.set_reactions(client)

    def set_reactions(self, client):

        # 投票ボタンとして使用するリアクションを設定

        self.vote_dict["positive"] = REACTION1
        self.vote_dict["negative"] = REACTION2
        self.vote_dict["stop"] = REACTION3

    def get_reactions(self):

        # 投票ボタン用リアクションを取得する
        # 戻り値:全てstr
        # react1:賛成リアクション react2:反対リアクション react3:終了リアクション

        react1 = self.vote_dict["positive"]
        react2 = self.vote_dict["negative"]
        react3 = self.vote_dict["stop"]
        return react1, react2, react3

    def get_reaction_info(self, reaction):

        # 押されたリアクションの役割を判断する
        # 戻り値:
        # react str:リアクションの種類
        # index int:Embed内の該当リアクションのインデックス番号

        positive, negative, stop = self.get_reactions()
        if reaction.emoji == positive:
            react = POSITIVE
            index = IDX_P
        elif reaction.emoji == negative:
            react = NEGATIVE
            index = IDX_N
        elif reaction.emoji == stop:
            react = STOP
            index = 999
        else:
            react = "None"
            index = 999
        return react, index

    def update_message_info(self, msg, prop, del_flg=False):

        # vote_dictを更新する
        # del_flgがTrueの場合は該当のインデックスを削除する

        if del_flg:
            self.vote_dict.pop(msg.id)
            self.vote_dict.pop(str(msg.id) + "Prop")
        else:
            self.vote_dict[msg.id] = msg
            self.vote_dict[str(msg.id) + "Prop"] = prop

    def get_message_info(self, msg):

        # vote_dictをメッセージIDで検索し情報を取得する
        # 戻り値:
        # message message:discordの投票用メッセージ
        # prop embed:該当メッセージのembed情報

        message = self.vote_dict.get(msg.id)
        prop = self.vote_dict.get(str(msg.id) + "Prop")
        return message, prop

    def is_already_voted(self, react, user, embed):

        # 別リアクションにすでに投票しているかを判断する

        if react == POSITIVE:
            index = IDX_N
        else:
            index = IDX_P
        if re.search(user.name, embed.to_dict()["fields"][index]["value"]):
            return True
        else:
            return False

    def create_embed(self, message):
        text = message.content.replace("/vote", "")
        embed = discord.Embed(title=TITLE + text)
        embed.set_author(name=message.author.name)
        embed.add_field(name=POSITIVE, value=message.author.name, inline=True)
        embed.add_field(name=NEGATIVE, value=INITIAL, inline=True)
        return embed

    def add_name_to_embed(self, embed, react, index, user):

        # embedの値にuserを追加する
        # 戻り値 embed embed:値編集後のembed

        if (embed.to_dict()["fields"][index]["value"]) == INITIAL:
            value = user.name
        else:
            value = "{}\n{}".format(embed.to_dict()["fields"][index]["value"], user.name)
        embed.set_field_at(index, name=react, value=value)
        return embed

    def remove_name_from_embed(self, embed, react, index, user):

        # embedの値からuserを削除する
        # 戻り値 embed embed:値編集後のembed

        splitted = embed.to_dict()["fields"][index]["value"].splitlines()
        try:
            splitted.remove(user.name)
            embed.set_field_at(index, name=react, value="\n".join(splitted) or INITIAL)
            return embed
        except:
            return embed

    def stop_voting(self, embed):

        # embedのフッターにSTOPのテキストを設定する

        embed.set_footer(text=STOP)
        return embed

    async def add_reactions(self, msg):

        # コルーチン
        # メッセージに投票ボタン用リアクションを追加する

        positive, negative, stop = self.get_reactions()
        await msg.add_reaction(positive)
        await msg.add_reaction(negative)
        await msg.add_reaction(stop)

    async def send_vote_message(self, message):

        # コルーチン
        # 投票用メッセージとボタン用リアクションを投稿し
        # vote_dictにメッセージ情報を設定する

        embed = self.create_embed(message)
        bot_msg = await message.channel.send(embed=embed)
        await self.add_reactions(bot_msg)
        self.update_message_info(bot_msg, embed)

    async def reflect_voting(self, reaction, user):

        # コルーチン
        # 投票リアクションの投票情報からメッセージを編集し投票結果を反映する

        message, embed = self.get_message_info(reaction.message)
        if not user.bot and message:
            react, index = self.get_reaction_info(reaction)
            if react in (POSITIVE, NEGATIVE):
                if embed.author.name != user.name and self.is_already_voted(react, user, embed) == False:
                    embed = self.add_name_to_embed(embed, react, index, user)
                    await message.edit(embed=embed)
                    self.update_message_info(reaction.message, embed)
            elif react == STOP:
                if embed.author.name == user.name:
                    embed = self.stop_voting(embed)
                    await message.edit(embed=embed)
                    self.update_message_info(reaction.message, embed, del_flg=True)

    async def cancel_voting(self, reaction, user):

        # コルーチン
        # 投票リアクションの削除情報からメッセージを編集し投票を取り消す

        message, embed = self.get_message_info(reaction.message)
        if message and embed.author.name != user.name:
            react, index = self.get_reaction_info(reaction)
            if react in (POSITIVE, NEGATIVE):
                embed = self.remove_name_from_embed(embed, react, index, user)
                await message.edit(embed=embed)
                self.update_message_info(reaction.message, embed)
