#   Copyright © 2017 Joaquim Monteiro
#
#   This file is part of USBMaker.
#
#   USBMaker is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   USBMaker is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with USBMaker.  If not, see <https://www.gnu.org/licenses/>.

import subprocess


def parse_passwd():
    passwd = subprocess.check_output(['getent', 'passwd']).decode()
    passwd_list = list()

    for user in passwd.strip().split('\n'):
        user_list = user.split(':')
        passwd_list.append(user_list)
    return passwd_list


def get_home_from_username(username):
    passwd = parse_passwd()
    for user in passwd:
        if user[0] == username:
            return user[5]
    raise UserNotFoundError


def get_home_from_uid(uid):
    passwd = parse_passwd()
    for user in passwd:
        if user[2] == uid:
            return user[5]
    raise UserNotFoundError


class UserNotFoundError(Exception):
    pass
