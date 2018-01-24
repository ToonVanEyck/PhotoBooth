import hashlib

event_name = "PhotoVoucher"
nr_of_codes = 15
def gen_vouchers(name,nr):
    vouchers = []
    for x in range(0, nr):
        voucher_id=(str(name+":"+str(x)))
        voucher_hash=hashlib.sha224(voucher_id.encode()).hexdigest()
        vouchers.append((voucher_id,voucher_hash))
    return vouchers
