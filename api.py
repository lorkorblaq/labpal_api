from flask import Flask, request, jsonify, render_template, Blueprint
from flask_restful import Api
from flask_cors import CORS
# from items_api import *  # Import your resources
# from put_in_use_api import *
# from user_api import *
# from channels_api import *
# from lot_exp_api import *
from end_points.items_api import *
from end_points.put_in_use_api import *
from end_points.user_api import *
from end_points.channels_api import *
from end_points.lot_exp_api import *
from end_points.messenger_api import *
from end_points.organisation import *
from end_points.events import *
from end_points.to_do import *
from end_points.billing import *
from end_points.webhook import *
from end_points.shipments import *
from end_points.machines import *
from end_points.org_api import *
from end_points.admin import Health

app = Flask(__name__)
api = Api(app)
CORS(app)


api.add_resource(Health, "/health")
#organisation
api.add_resource(OrgGetLabs, "/api/labs/get/<string:user_id>/")


#subscription
api.add_resource(Customer, "/api/customer/<string:org_id>/")
api.add_resource(Subscription, "/api/subscription/<string:org_id>/<string:plan>/")
api.add_resource(TransactionSuccess, "/api/transactions/success/<string:org_id>/")
api.add_resource(Transactions, "/api/transactions/<string:org_id>/")




#users
api.add_resource(UserPush, "/api/user/push/")
api.add_resource(UserPut, "/api/user/put/<string:user_id>/")
api.add_resource(UserDel, "/api/user/del/<string:user_id>/")
api.add_resource(UserGetOne, "/api/user/get/<string:user_id>/")
api.add_resource(UsersGetAll, "/api/users/get/")
api.add_resource(UploadImage, "/api/user-image/<string:user_id>/")


#events
api.add_resource(EventPush, "/api/event/push/<string:user_id>/<string:lab_name>/<string:event_type>/")
api.add_resource(EventPut, "/api/event/put/<string:user_id>/<string:lab_name>/<string:event_id>/")
api.add_resource(EventDel, "/api/event/del/<string:user_id>/<string:lab_name>/<string:event_id>/")
api.add_resource(EventGetOne, "/api/event/get/<string:user_id>/<string:lab_name>/<string:event_id>/")
api.add_resource(EventGetAll, "/api/events/get/<string:user_id>/<string:lab_name>/<string:event_type>/")

api.add_resource(ToDoPush, "/api/to-do/push/<string:user_id>/")
api.add_resource(ToDoPut, "/api/to-do/put/<string:user_id>/<string:date>/")
api.add_resource(ToDoGetOne, "/api/to-do/get/<string:user_id>/<string:date>/")
api.add_resource(ToDoGetAll, "/api/to-do/get-all/<string:user_id>/")
api.add_resource(ToDoDeleteDate, "/api/to-do/del/<string:user_id>/<string:date>/")
# api.add_resource(ToDoSaveOrder, '/to-do/<string:user_id>/save-order/')

#organisations
api.add_resource(OrganisationPush, "/api/org/push/")
api.add_resource(GetOrganisation, "/api/org/get/<string:name>/")

#items
api.add_resource(ItemsResource, "/api/items/get/<string:user_id>/<string:lab_name>/")
api.add_resource(ItemsPush, "/api/items/push/<string:user_id>/<string:lab_name>/")
api.add_resource(ItemsBulkPush, "/api/items/bulkpush/<string:user_id>/<string:lab_name>/")
api.add_resource(ItemsPut, "/api/item/put/<string:user_id>/<string:lab_name>/")
api.add_resource(ItemsRequisite, "/api/items/requisite/<string:user_id>/<string:lab_name>/")
api.add_resource(ItemsDeleteResource, "/api/items/deleteall/<string:user_id>/<string:lab_name>/")

#machines
api.add_resource(MachinePush, "/api/machines/push/<string:user_id>/<string:lab_name>/")
api.add_resource(MachineBulkPush, "/api/machines/bulkpush/<string:user_id>/<string:lab_name>/")
api.add_resource(MachinePut, "/api/machine/put/<string:user_id>/<string:lab_name>/")
api.add_resource(MachineGetOne, "/api/machine/get/<string:user_id>/<string:lab_name>/<string:machine_id>/")
api.add_resource(MachineGetAll, "/api/machines/get/<string:user_id>/<string:lab_name>/")
api.add_resource(MachineDel, "/api/machines/deleteall/<string:user_id>/<string:lab_name>/")


#put in use
api.add_resource(P_in_usePush, "/api/piu/push/<string:user_id>/<string:lab_name>/")
api.add_resource(P_in_usePut, "/api/piu/put/<string:user_id>/<string:lab_name>/<string:piu_id>/")
api.add_resource(P_in_useDelete, "/api/piu/delete/<string:user_id>/<string:lab_name>/<string:piu_id>/")
api.add_resource(P_in_useGetOne, "/api/piu/get/<string:user_id>/<string:lab_name>/<string:piu_id>/")
api.add_resource(P_in_useGetAll, "/api/piu/get/<string:user_id>/<string:lab_name>/")

#channel
api.add_resource(ChannelPush, "/api/channel/push/<string:user_id>/<string:lab_name>/")
api.add_resource(ChannelPut, "/api/channel/put/<string:user_id>/<string:lab_name>/<string:channel_id>/")
api.add_resource(ChannelDel, "/api/channel/delete/<string:user_id>/<string:lab_name>/<string:channel_id>/")
api.add_resource(ChannelGetOne, "/api/channel/get/<string:user_id>/<string:lab_name>/<string:channel_id>/")
api.add_resource(ChannelGetAll, "/api/channels/get/<string:user_id>/<string:lab_name>/")

#shipments
api.add_resource(ShipmentsPush, "/api/shipments/push/<string:user_id>/<string:lab_name>/")
api.add_resource(ShipmentsPut, "/api/shipments/put/<string:user_id>/<string:lab_name>/")
api.add_resource(ShipmentsDel, "/api/shipments/delete/<string:user_id>/<string:lab_name>/<string:shipments_id>/")
api.add_resource(ShipmentsGetOne, "/api/shipments/get/<string:user_id>/<string:lab_name>/<string:shipments_id>/")
api.add_resource(ShipmentsGetAll, "/api/shipments/get/<string:user_id>/<string:lab_name>/")

#lot exp
api.add_resource(Lot_exp_Get, "/api/lotexp/get/<string:user_id>/<string:lab_name>/")
api.add_resource(Lot_exp_Push, "/api/lotexp/push/<string:user_id>/<string:lab_name>/")

#messenger
api.add_resource(CreatePot, '/api/pot/create/<string:user_id>/')
api.add_resource(GetPots, '/api/pots/get/')
api.add_resource(GetMyPots, '/api/pots/get/<string:user_id>/')

api.add_resource(GetConversations, '/api/conversations/get/<string:user_id>/')
api.add_resource(GetPrivateMessages, '/api/gpm/<string:sender_id>/<string:recipient_id>/')
api.add_resource(GetPotMessages, '/api/gpotm/<string:pot_id>/')

api.add_resource(JoinPot, '/api/pot/join/<string:user_id>/<string:pot_id>/')
api.add_resource(LeavePot, '/api/pot/leave/<string:user_id>/<string:pot_id>/')
api.add_resource(DeletePot, '/api/pot/delete/<string:user_id>/<string:pot_id>/')

api.add_resource(PushPotMessage, '/api/pot/message/push/<string:sender_id>/<string:pot_id>/')
api.add_resource(PushGlobalMessage, '/api/pot/global_message/push/<string:sender_id>/<string:pot_id>/')
api.add_resource(PushPrivateMessage, '/api/pm/push/<string:sender_id>/<string:recipient_id>/')

api.add_resource(AddContact, '/api/contact/add/<string:user_id>/<string:contact_id>/')
api.add_resource(DeleteContact, '/api/contact/delete/<string:user_id>/<string:contact_id>/')

api.add_resource(Webhook, '/api/webhook/')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
